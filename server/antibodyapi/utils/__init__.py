import os
import globus_sdk
import requests
from flask import (
    Flask, abort, g, jsonify, make_response, redirect,
    session, request, render_template, url_for
)
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
# pylint: disable=no-name-in-module
from psycopg2.errors import UniqueViolation

from requests.packages.urllib3.exceptions import InsecureRequestWarning # pylint: disable=import-error
requests.packages.urllib3.disable_warnings(category = InsecureRequestWarning) # pylint: disable=no-member

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Missing: avr_filename, avr_uuid
def base_antibody_query():
    return '''
SELECT
    a.antibody_uuid,
    a.protocols_io_doi,
    a.uniprot_accession_number,
    a.target_name, a.rrid,
    a.antibody_name, a.host_organism,
    a.clonality, v.name,
    a.catalog_number, a.lot_number,
    a.recombinant, a.organ_or_tissue,
    a.hubmap_platform, a.submitter_orciid,
    a.created_timestamp,
    a.created_by_user_displayname, a.created_by_user_email,
    a.created_by_user_sub, a.group_uuid
FROM antibodies a
JOIN vendors v ON a.vendor_id = v.id
'''

def base_antibody_query_result_to_json(antibody) -> dict:
    ant = {
        'antibody_uuid': antibody[0],
        'protocols_io_doi': antibody[1],
        'uniprot_accession_number': antibody[2],
        'target_name': antibody[3],
        'rrid': antibody[4],
        'antibody_name': antibody[5],
        'host_organism': antibody[6],
        'clonality': antibody[7],
        'vendor': antibody[8],
        'catalog_number': antibody[9],
        'lot_number': antibody[10],
        'recombinant': antibody[11],
        'organ_or_tissue': antibody[12],
        'hubmap_platform': antibody[13],
        'submitter_orciid': antibody[14],
        # 'created_timestamp': antibody[15]
        'created_by_user_displayname': antibody[16],
        'created_by_user_email': antibody[17],
        'created_by_user_sub': antibody[18],
        'group_uuid': antibody[19]
    }
    return ant

def find_or_create_vendor(cursor, name):
    cursor.execute('SELECT id FROM vendors WHERE UPPER(name) = %s', (name.upper(),))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        cursor.execute('INSERT INTO vendors (name) VALUES (%s) RETURNING id', (name,))
        return cursor.fetchone()[0]

def get_cursor(app):
    if 'connection' not in g:
        conn = psycopg2.connect(
            dbname=app.config['DATABASE_NAME'],
            user=app.config['DATABASE_USER'],
            password=app.config['DATABASE_PASSWORD'],
            host=app.config['DATABASE_HOST']
        )
        g.connection = conn # pylint: disable=assigning-non-slot
        g.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return g.connection.cursor()

def get_file_uuid(ingest_api_url, upload_folder, antibody_uuid, file):
    filename = secure_filename(file.filename)
    file.save(os.path.join(upload_folder, filename))
    req = requests.post(
        '%s/file-upload' % (ingest_api_url,),
        headers={
            'authorization': 'Bearer %s' % session['groups_access_token']
        },
        files={'file':
            (
                file.filename,
                open(os.path.join(upload_folder, filename), 'rb'),
                'application/pdf'
            )
        },
        verify=False
    )
    temp_file_id = req.json()['temp_file_id']

    req2 = requests.post(
        '%s/file-commit' % (ingest_api_url,),
        headers={
            'authorization': 'Bearer %s' % session['groups_access_token']
        },
        json={
            'entity_uuid': antibody_uuid,
            'temp_file_id': temp_file_id,
            'user_token': session['groups_access_token']
        },
        verify=False
    )
    return req2.json()['file_uuid']

def get_group_id(ingest_api_url, group_id=None):
    req = requests.get(
        '%s/metadata/usergroups' % (ingest_api_url,),
        headers={
            'authorization': 'Bearer %s' % session['groups_access_token']
        },
        verify=False
    )
    groups = {g['uuid']: g['data_provider'] for g in req.json()['groups']}

    if group_id:
        if groups.get(group_id):
            return group_id
        return None

    if list(groups.values()).count(True) != 1:
        return None

    for uuid, data_provider in groups.items():
        if data_provider:
            return uuid

    return None

def get_data_provider_groups(ingest_api_url):
    req = requests.get(
        '%s/metadata/usergroups' % (ingest_api_url,),
        headers={
            'authorization': 'Bearer %s' % session['groups_access_token']
        },
        verify=False
    )
    groups = {g['uuid']: { 'displayname': g['displayname'], 'data_provider': g['data_provider'] } for g in req.json()['groups']}

    data_provider_groups = []
    for uuid, group_info in groups.items():
        if group_info['data_provider']:
            data_provider_groups.append([uuid, group_info['displayname']])

    return data_provider_groups

def get_hubmap_uuid(uuid_api_url):
    req = requests.post(
        '%s/hmuuid' % (uuid_api_url,),
        headers={
            'Content-Type': 'application/json',
            'authorization': 'Bearer %s' % session['groups_access_token']
        },
        json={'entity_type': 'AVR'},
        verify=False
    )
    return req.json()[0]['uuid']

def get_user_info(token):
    auth_token = token.by_resource_server['auth.globus.org']['access_token']
    auth_client = globus_sdk.AuthClient(authorizer=globus_sdk.AccessTokenAuthorizer(auth_token))
    return auth_client.oauth2_userinfo()

def insert_query():
    return '''
INSERT INTO antibodies (
    antibody_uuid,
    protocols_io_doi,
    uniprot_accession_number,
    target_name, rrid,
    antibody_name, host_organism,
    clonality, vendor_id,
    catalog_number, lot_number,
    recombinant, organ_or_tissue,
    hubmap_platform, submitter_orciid,
    created_timestamp,
    created_by_user_displayname, created_by_user_email,
    created_by_user_sub, group_uuid
) 
VALUES (
    %(antibody_uuid)s,
    %(protocols_io_doi)s,
    %(uniprot_accession_number)s,
    %(target_name)s,
    %(rrid)s,
    %(antibody_name)s,
    %(host_organism)s,
    %(clonality)s,
    %(vendor_id)s,
    %(catalog_number)s,
    %(lot_number)s,
    %(recombinant)s,
    %(organ_or_tissue)s,
    %(hubmap_platform)s,
    %(submitter_orciid)s,
    EXTRACT(epoch FROM NOW()),
    %(created_by_user_displayname)s,
    %(created_by_user_email)s,
    %(created_by_user_sub)s,
    %(group_uuid)s
) RETURNING id
'''

def insert_query_with_avr_file_and_uuid():
    return '''
INSERT INTO antibodies (
    antibody_uuid,
    avr_uuid,
    avr_filename,
    protocols_io_doi,
    uniprot_accession_number,
    target_name,
    rrid,
    antibody_name,
    host_organism,
    clonality,
    vendor_id,
    catalog_number,
    lot_number,
    recombinant,
    organ_or_tissue,
    hubmap_platform,
    submitter_orciid,
    created_timestamp,
    created_by_user_displayname,
    created_by_user_email,
    created_by_user_sub,
    group_uuid
) 
VALUES (
    %(antibody_uuid)s,
    %(avr_uuid)s,
    %(avr_filename)s,
    %(protocols_io_doi)s,
    %(uniprot_accession_number)s,
    %(target_name)s,
    %(rrid)s,
    %(antibody_name)s,
    %(host_organism)s,
    %(clonality)s,
    %(vendor_id)s,
    %(catalog_number)s,
    %(lot_number)s,
    %(recombinant)s,
    %(organ_or_tissue)s,
    %(hubmap_platform)s,
    %(submitter_orciid)s,
    EXTRACT(epoch FROM NOW()),
    %(created_by_user_displayname)s,
    %(created_by_user_email)s,
    %(created_by_user_sub)s,
    %(group_uuid)s
) RETURNING id
'''

def json_error(message, error_code):
    return make_response(jsonify(message=message), error_code)
