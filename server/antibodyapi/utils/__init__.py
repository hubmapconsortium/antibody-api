import os
import globus_sdk
import requests
from flask import (
    Flask, abort, g, jsonify, make_response, redirect,
    session, request, render_template, url_for
)
from enum import IntEnum, unique
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
# pylint: disable=no-name-in-module
from psycopg2.errors import UniqueViolation
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning # pylint: disable=import-error

requests.packages.urllib3.disable_warnings(category = InsecureRequestWarning) # pylint: disable=no-member

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# TODO: This is duplicated in 'scripts/utils/__init__.py'
@unique
class SI(IntEnum):
    ANTIBODY_UUID = 0
    AVR_FILENAME = 1
    AVR_UUID = 2
    PROTOCOLS_IO_DOI = 3
    UNIPROT_ACCESSION_NUMBER = 4
    TARGET_NAME = 5
    RRID = 6
    ANTIBODY_NAME = 7
    HOST_ORGANISM = 8
    CLONALITY = 9
    VENDOR_NAME = 10
    CATALOG_NUMBER = 11
    LOT_NUMBER = 12
    RECOMBINATE = 13
    ORGAN_OR_TISSSUE = 14
    HUBMAP_PLATFORM = 15
    SUBMITTER_ORCID = 16
    CREATED_TIMESTAMP = 17
    CREATED_BY_USER_DISPLAYNAME = 18
    CREATED_BY_USER_EMAIL = 19
    CREATED_BY_USER_SUB = 20
    GROUP_UUID = 21


QUERY = '''
SELECT
    a.antibody_uuid,
    a.avr_filename, a.avr_uuid,
    a.protocols_io_doi,
    a.uniprot_accession_number,
    a.target_name, a.rrid,
    a.antibody_name, a.host_organism,
    a.clonality, v.name,
    a.catalog_number, a.lot_number,
    a.recombinant, a.organ_or_tissue,
    a.hubmap_platform, a.submitter_orcid,
    a.created_timestamp,
    a.created_by_user_displayname, a.created_by_user_email,
    a.created_by_user_sub, a.group_uuid
FROM antibodies a
JOIN vendors v ON a.vendor_id = v.id
'''


def base_antibody_query():
    return QUERY


def base_antibody_query_result_to_json(antibody) -> dict:
    ant = {
        'antibody_uuid': antibody[SI.ANTIBODY_UUID].replace('-', ''),
        'protocols_io_doi': antibody[SI.PROTOCOLS_IO_DOI],
        'uniprot_accession_number': antibody[SI.UNIPROT_ACCESSION_NUMBER],
        'target_name': antibody[SI.TARGET_NAME],
        'rrid': antibody[SI.RRID],
        'antibody_name': antibody[SI.ANTIBODY_NAME],
        'host_organism': antibody[SI.HOST_ORGANISM],
        'clonality': antibody[SI.CLONALITY],
        'vendor': antibody[SI.VENDOR_NAME],
        'catalog_number': antibody[SI.CATALOG_NUMBER],
        'lot_number': antibody[SI.LOT_NUMBER],
        'recombinant': antibody[SI.RECOMBINATE],
        'organ_or_tissue': antibody[SI.ORGAN_OR_TISSSUE],
        'hubmap_platform': antibody[SI.HUBMAP_PLATFORM],
        'submitter_orcid': antibody[SI.SUBMITTER_ORCID],
        # 'created_timestamp': antibody[15]
        'created_by_user_displayname': antibody[SI.CREATED_BY_USER_DISPLAYNAME],
        'created_by_user_email': antibody[SI.CREATED_BY_USER_EMAIL],
        'created_by_user_sub': antibody[SI.CREATED_BY_USER_SUB],
        'group_uuid': antibody[SI.GROUP_UUID].replace('-', '')
    }
    if antibody[SI.AVR_UUID] is not None:
        ant['avr_filename'] = antibody[SI.AVR_FILENAME]
        ant['avr_uuid'] = antibody[SI.AVR_UUID].replace('-', '')
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


def get_file_uuid(ingest_api_url: str, upload_folder, antibody_uuid, file):
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
    if req.status_code != 201:
        logger.debug(f"utils/get_file_uuid: response.status_code {req.status_code}")
        abort(json_error(f"Internal error caused when trying to accessing server '{ingest_api_url}'; status: {req.status_code}", 406))

    temp_file_id = req.json()['temp_file_id']
    logger.debug(f"utils/get_file_uuid: temp_file_id = {temp_file_id}")
    logger.debug(f"utils/get_file_uuid: antibody_uuid = {antibody_uuid}")

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
    if req.status_code != 201:
        logger.debug(f"utils/get_file_uuid: response.status_code {req.status_code}")
        abort(json_error(f"Internal error caused when trying to accessing server '{ingest_api_url}'; status: {req2.status_code}", 406))

    file_uuid = req2.json()['file_uuid']
    logger.debug(f"utils/get_file_uuid: file_uuid = {file_uuid}")
    return file_uuid


def get_group_id(ingest_api_url: str, group_id=None):
    req = requests.get(
        '%s/metadata/usergroups' % (ingest_api_url,),
        headers={
            'authorization': 'Bearer %s' % session['groups_access_token']
        },
        verify=False
    )
    if req.status_code != 200:
        logger.debug(f"utils/get_group_id: response.status_code {req.status_code}")
        abort(json_error(f"Internal error caused when trying to accessing server '{ingest_api_url}'; status: {req.status_code}", 406))

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


def get_data_provider_groups(ingest_api_url: str):
    req = requests.get(
        '%s/metadata/usergroups' % (ingest_api_url,),
        headers={
            'authorization': 'Bearer %s' % session['groups_access_token']
        },
        verify=False
    )
    if req.status_code != 200:
        logger.debug(f"utils/get_data_provider_groups: response.status_code {req.status_code}")
        abort(json_error(f"Internal error caused when trying to accessing server '{ingest_api_url}'; status: {req.status_code}", 406))

    groups = {g['uuid']: { 'displayname': g['displayname'], 'data_provider': g['data_provider'] } for g in req.json()['groups']}

    data_provider_groups = []
    for uuid, group_info in groups.items():
        if group_info['data_provider']:
            data_provider_groups.append([uuid, group_info['displayname']])

    return data_provider_groups


def get_hubmap_uuid(uuid_api_url: str):
    req = requests.post(
        '%s/hmuuid' % (uuid_api_url,),
        headers={
            'Content-Type': 'application/json',
            'authorization': 'Bearer %s' % session['groups_access_token']
        },
        json={'entity_type': 'AVR'},
        verify=False
    )
    if req.status_code != 200:
        logger.debug(f"utils/get_hubmap_uuid: response.status_code {req.status_code}")
        abort(json_error(f"Internal error caused when trying to accessing server '{uuid_api_url}'; status: {req.status_code}", 406))

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
    hubmap_platform, submitter_orcid,
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
    %(submitter_orcid)s,
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
    submitter_orcid,
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
    %(submitter_orcid)s,
    EXTRACT(epoch FROM NOW()),
    %(created_by_user_displayname)s,
    %(created_by_user_email)s,
    %(created_by_user_sub)s,
    %(group_uuid)s
) RETURNING id
'''


def json_error(message: str, error_code: int):
    logger.info(f'JSON_ERROR Response; message: {message}; error_code: {error_code}')
    return make_response(jsonify(message=message), error_code)
