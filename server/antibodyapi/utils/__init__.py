import os
import globus_sdk
import requests
from flask import abort, g, jsonify, make_response,  session
from enum import IntEnum, unique
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2._psycopg import connection
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning # pylint: disable=import-error

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning) # pylint: disable=no-member

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'tsv'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# TODO: This is duplicated in 'scripts/utils/__init__.py'
@unique
class SI(IntEnum):
    ANTIBODY_UUID = 0
    AVR_PDF_FILENAME = 1
    AVR_PDF_UUID = 2
    PROTOCOL_DOI = 3
    UNIPROT_ACCESSION_NUMBER = 4
    TARGET_SYMBOL = 5
    RRID = 6
    HOST = 7
    CLONALITY = 8
    VENDOR_NAME = 9
    CATALOG_NUMBER = 10
    LOT_NUMBER = 11
    RECOMBINANT = 12
    ORGAN = 13
    METHOD = 14
    AUTHOR_ORCIDS = 15
    HGNC_ID = 16
    ISOTYPE = 17
    CONCENTRATION_VALUE = 18
    DILUTION_FACTOR = 19
    CONJUGATE = 20
    TISSUE_PRESERVATION = 21
    CYCLE_NUMBER = 22
    FLUORESCENT_REPORTER = 23
    MANUSCRIPT_DOI = 24
    VENDOR_AFFILIATION = 25
    ORGAN_UBERON_ID = 26
    ANTIGEN_RETRIEVAL = 27
    OMAP_ID = 28
    CREATED_TIMESTAMP = 29
    CREATED_BY_USER_DISPLAYNAME = 30
    CREATED_BY_USER_EMAIL = 31
    CREATED_BY_USER_SUB = 32
    GROUP_UUID = 33
    CLONE_ID = 34
    ANTIBODY_HUBMAP_ID = 35
    PREVIOUS_VERSION_ID = 36
    NEXT_VERSION_ID = 37
    PREVIOUS_VERSION_PDF_UUID = 38
    PREVIOUS_VERSION_PDF_FILENAME = 39


# THESE MUST MATCH THE ORDER IN THE ""SI"" CLASS!!!
QUERY = '''
SELECT
    a.antibody_uuid,
    a.avr_pdf_filename, a.avr_pdf_uuid,
    a.protocol_doi, a.uniprot_accession_number,
    a.target_symbol, a.rrid, a.host,
    a.clonality, v.vendor_name,
    a.catalog_number, a.lot_number, a.recombinant, a.organ,
    a.method, a.author_orcids, a.hgnc_id, a.isotype,
    a.concentration_value, a.dilution_factor, a.conjugate,
    a.tissue_preservation, a.cycle_number, a.fluorescent_reporter,
    a.manuscript_doi, a.vendor_affiliation, a.organ_uberon_id,
    a.antigen_retrieval, a.omap_id,
    a.created_timestamp,
    a.created_by_user_displayname, a.created_by_user_email,
    a.created_by_user_sub, a.group_uuid,
    a.clone_id,
    a.antibody_hubmap_id, a.previous_version_id, a.next_version_id,
    a.previous_version_pdf_uuid, a.previous_version_pdf_filename, a.next_version_id
FROM antibodies a
JOIN vendors v ON a.vendor_id = v.id
'''


def base_antibody_query():
    return QUERY


def base_antibody_query_result_to_json(antibody) -> dict:
    ant = {
        'antibody_uuid': antibody[SI.ANTIBODY_UUID].replace('-', ''),
        'antibody_hubmap_id': antibody[SI.ANTIBODY_HUBMAP_ID],
        'protocol_doi': antibody[SI.PROTOCOL_DOI],
        'uniprot_accession_number': antibody[SI.UNIPROT_ACCESSION_NUMBER],
        'target_symbol': antibody[SI.TARGET_SYMBOL],
        'rrid': antibody[SI.RRID],
        'host': antibody[SI.HOST],
        'clonality': antibody[SI.CLONALITY],
        'clone_id': antibody[SI.CLONE_ID],
        'vendor_name': antibody[SI.VENDOR_NAME],
        'catalog_number': antibody[SI.CATALOG_NUMBER],
        'lot_number': antibody[SI.LOT_NUMBER],
        'recombinant': antibody[SI.RECOMBINANT],
        'organ': antibody[SI.ORGAN],
        'method': antibody[SI.METHOD],
        'author_orcids': antibody[SI.AUTHOR_ORCIDS],
        'hgnc_id': antibody[SI.HGNC_ID],
        'isotype': antibody[SI.ISOTYPE],
        'concentration_value': antibody[SI.CONCENTRATION_VALUE],
        'dilution_factor': antibody[SI.DILUTION_FACTOR],
        'conjugate': antibody[SI.CONJUGATE],
        'tissue_preservation': antibody[SI.TISSUE_PRESERVATION],
        'cycle_number': antibody[SI.CYCLE_NUMBER],
        'fluorescent_reporter': antibody[SI.FLUORESCENT_REPORTER],
        'manuscript_doi': antibody[SI.MANUSCRIPT_DOI],
        'vendor_affiliation': antibody[SI.VENDOR_AFFILIATION],
        'organ_uberon_id': antibody[SI.ORGAN_UBERON_ID],
        'antigen_retrieval': antibody[SI.ANTIGEN_RETRIEVAL],
        'omap_id': antibody[SI.OMAP_ID],
        # 'created_timestamp': antibody[SI.CREATED_TIMESTAMP]
        'created_by_user_displayname': antibody[SI.CREATED_BY_USER_DISPLAYNAME],
        'created_by_user_email': antibody[SI.CREATED_BY_USER_EMAIL],
        'created_by_user_sub': antibody[SI.CREATED_BY_USER_SUB],
        'group_uuid': antibody[SI.GROUP_UUID].replace('-', ''),
        'previous_version_id': antibody[SI.PREVIOUS_VERSION_ID],
        'next_version_id': antibody[SI.NEXT_VERSION_ID],
        'previous_version_pdf_uuid': antibody[SI.PREVIOUS_VERSION_PDF_UUID],
        'previous_version_pdf_filename': antibody[SI.PREVIOUS_VERSION_PDF_FILENAME]
    }
    if antibody[SI.AVR_PDF_UUID] is not None:
        ant['avr_pdf_uuid'] = antibody[SI.AVR_PDF_UUID].replace('-', '')
        ant['avr_pdf_filename'] = antibody[SI.AVR_PDF_FILENAME]
    return ant


def find_or_create_vendor(cursor, vendor_name):
    cursor.execute('SELECT id FROM vendors WHERE UPPER(vendor_name) = %s', (vendor_name.upper(),))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        cursor.execute('INSERT INTO vendors (vendor_name) VALUES (%s) RETURNING id', (vendor_name,))
        return cursor.fetchone()[0]


def get_cursor(app):
    """
    Reuse an existing connection after testing to see that it still works.
    If the connection is no longer valid, or was never established, then make one.

    Return an error message and a status_code == 502 if there is a problem creating a connection,
    otherwise return a cursor.
    """
    host: str = app.config['DATABASE_HOST']
    user: str = app.config['DATABASE_USER']
    dbname: str = app.config['DATABASE_NAME']
    password: str = app.config['DATABASE_PASSWORD']
    if 'connection' in g:
        # Test to see if the connection still works...
        try:
            # NOTE: connection.isolation_level no longer actually calls the database
            cur = g.connection.cursor()
            cur.execute('SELECT 1')
            cur.close()
        except psycopg2.OperationalError:
            logger.error("Connectionn to PosgreSQL database is no longer valid")
            g.connection = None
    if 'connection' not in g or g.connection is None or g.connection.closed != 0:
        # Have not connected or the connection is now broken or closed...
        logger.info(f"Connecting to PosgreSQL database; host: {host}, user: {user}, dbname: {dbname}")
        try:
            conn: connection = psycopg2.connect(host=host, user=user, dbname=dbname, password=password)
        except psycopg2.Error as e:
            abort(json_error(f"Unable to connect to PosgreSQL database; error: {e}", 502))
        logger.info("Successfully connected to PosgreSQL database")
        g.connection = conn
        g.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return g.connection.cursor()


def get_file_uuid(ingest_api_url: str, upload_folder: str, antibody_uuid: str, file) -> str:
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
    if req2.status_code not in (200, 201):
        logger.debug(f"utils/get_file_uuid: response.status_code {req.status_code}")
        abort(json_error(f"Internal error caused when trying to accessing server '{ingest_api_url}'; status: {req2.status_code}", 406))

    file_uuid = req2.json()['file_uuid']
    logger.debug(f"utils/get_file_uuid: after file-commit; file_uuid = {file_uuid}")
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


def get_hubmap_uuid(uuid_api_url: str) -> dict:
    url: str = f'{uuid_api_url}/hmuuid'
    req = requests.post(
        url,
        headers={
            'Content-Type': 'application/json',
            'authorization': 'Bearer %s' % session['groups_access_token']
        },
        json={'entity_type': 'AVR'},
        verify=False
    )
    if req.status_code != 200:
        abort(json_error(f"Error accessing '{url}'; status: {req.status_code}", 406))

    logger.debug(f"get_hubmap_uuid(); url={url}; req.json={req.json()}")
    return req.json()[0]


def get_user_info(token):
    auth_token = token.by_resource_server['auth.globus.org']['access_token']
    auth_client = globus_sdk.AuthClient(authorizer=globus_sdk.AccessTokenAuthorizer(auth_token))
    return auth_client.oauth2_userinfo()


def update_next_version_query():
    return '''
UPDATE antibodies
    SET next_version_id = %(next_version_id)s
    WHERE antibody_hubmap_id = %(previous_version_id)s
'''

def fetch_previous_version_pdf_uuid_query():
    return '''
        SELECT avr_pdf_uuid, avr_pdf_filename
        FROM antibodies
        WHERE antibody_hubmap_id = %(previous_version_id)s
    '''


def insert_query():
    return '''
INSERT INTO antibodies (
    antibody_uuid,
    protocol_doi, uniprot_accession_number,
    target_symbol, rrid, host,
    clonality, clone_id, vendor_id,
    catalog_number, lot_number, recombinant, organ,
    method, author_orcids, hgnc_id, isotype,
    concentration_value, dilution_factor, conjugate,
    tissue_preservation, cycle_number, fluorescent_reporter,
    manuscript_doi, vendor_affiliation, organ_uberon_id,
    antigen_retrieval, omap_id,
    created_timestamp,
    created_by_user_displayname, created_by_user_email,
    created_by_user_sub, group_uuid,
    previous_version_id, antibody_hubmap_id, previous_version_pdf_uuid, previous_version_pdf_filename
) 
VALUES (
    %(antibody_uuid)s,
    %(protocol_doi)s, %(uniprot_accession_number)s,
    %(target_symbol)s, %(rrid)s, %(host)s,
    %(clonality)s, %(clone_id)s, %(vendor_id)s,
    %(catalog_number)s, %(lot_number)s, %(recombinant)s, %(organ)s,
    %(method)s, %(author_orcids)s, %(hgnc_id)s, %(isotype)s,
    %(concentration_value)s, %(dilution_factor)s, %(conjugate)s,
    %(tissue_preservation)s, %(cycle_number)s, %(fluorescent_reporter)s,
    %(manuscript_doi)s, %(vendor_affiliation)s, %(organ_uberon_id)s,
    %(antigen_retrieval)s, %(omap_id)s,
    EXTRACT(epoch FROM NOW()),
    %(created_by_user_displayname)s, %(created_by_user_email)s,
    %(created_by_user_sub)s, %(group_uuid)s,
    %(previous_version_id)s, %(antibody_hubmap_id)s, %(previous_version_pdf_uuid)s, %(previous_version_pdf_filename)s
) RETURNING id
'''


def insert_query_with_avr_file_and_uuid():
    return '''
INSERT INTO antibodies (
    antibody_uuid,
    avr_pdf_uuid, avr_pdf_filename,
    protocol_doi, uniprot_accession_number,
    target_symbol, rrid, host,
    clonality, clone_id, vendor_id,
    catalog_number, lot_number, recombinant, organ,
    method, author_orcids, hgnc_id, isotype,
    concentration_value, dilution_factor, conjugate,
    tissue_preservation, cycle_number, fluorescent_reporter,
    manuscript_doi, vendor_affiliation, organ_uberon_id,
    antigen_retrieval, omap_id,
    created_timestamp,
    created_by_user_displayname, created_by_user_email,
    created_by_user_sub, group_uuid,
    previous_version_id, antibody_hubmap_id, previous_version_pdf_uuid, previous_version_pdf_filename
) 
VALUES (
    %(antibody_uuid)s,
    %(avr_pdf_uuid)s, %(avr_pdf_filename)s,
    %(protocol_doi)s, %(uniprot_accession_number)s,
    %(target_symbol)s, %(rrid)s, %(host)s,
    %(clonality)s, %(clone_id)s, %(vendor_id)s,
    %(catalog_number)s, %(lot_number)s, %(recombinant)s, %(organ)s,
    %(method)s, %(author_orcids)s, %(hgnc_id)s, %(isotype)s,
    %(concentration_value)s, %(dilution_factor)s, %(conjugate)s,
    %(tissue_preservation)s, %(cycle_number)s, %(fluorescent_reporter)s,
    %(manuscript_doi)s, %(vendor_affiliation)s, %(organ_uberon_id)s,
    %(antigen_retrieval)s, %(omap_id)s,
    EXTRACT(epoch FROM NOW()),
    %(created_by_user_displayname)s, %(created_by_user_email)s,
    %(created_by_user_sub)s, %(group_uuid)s,
    %(previous_version_id)s, %(antibody_hubmap_id)s, %(previous_version_pdf_uuid)s, %(previous_version_pdf_filename)s
) RETURNING id
'''


def json_error(message: str, error_code: int):
    logger.info(f'JSON_ERROR Response; message: {message}; error_code: {error_code}')
    return make_response(jsonify(message=message), error_code)
