from flask import abort, Blueprint, current_app, jsonify, make_response, request, session
import requests
from psycopg2.errors import UniqueViolation #pylint: disable=no-name-in-module
from antibodyapi.utils import (
    find_or_create_vendor, get_cursor,
    get_hubmap_uuid, insert_query, json_error
)
from antibodyapi.utils.elasticsearch import index_antibody
import logging

logger = logging.getLogger(__name__)

save_antibody_blueprint = Blueprint('save_antibody', __name__)


def save_antibody_isauth_check() -> bool:
    """
    If they are associated with the Globus HUBMAP_AVR_UPLOADERS_GROUP_ID (found in ./instance/app.conf)
    https://app.globus.org/groups/1cb77e93-4e50-11ee-91d3-a71fdaeb2f9c/about
    then return True otherwise return False.

    This can get called in one of three ways:
    1) The user has not authenticated. Anyone is permitted to access this app without
    logging in through Globus. So, then will NOT have a BEARER token.
    In this case always return False.
    2) The user has anthenticated, but the token is expired or otherwise invalid.
    In this case the call to ingest-api will return something other than a 200.
    In this case always return False.
    3) The user has authenticated, and the token is valid.
    In this case the call to ingest-api will succeed (200) and a list of groups will
    be returned. If the user has the appropriate group, then return True, otherwise False.
    """
    authorization: str = request.headers.get('Authorization')    # Bearer YourTokenHere
    if authorization is None:
        logger.info(f"save_antibody_isauth_check: Bearer token not found")
        return False
    authorization_parts: list = authorization.split()
    if len(authorization_parts) != 2 or authorization_parts[0].lower() != "bearer":
        logger.info(f"save_antibody_isauth_check: Bearer token broken")
        return False
    token: str = authorization_parts[1]
    url: str = f"{current_app.config['INGEST_API_URL']}/metadata/usergroups"
    resp = requests.get(url,
        headers={
            'authorization': 'Bearer %s' % token
        },
        verify=False
    )
    if resp.status_code != 200:
        if resp.status_code == 401:
            logger.info(f"save_antibody_isauth_check: {url} indicates the user is unauthorized")
        return False
    group_uuids: list = [x['uuid'] for x in resp.json()['groups']]
    is_auth_group_id: str = current_app.config['HUBMAP_AVR_UPLOADERS_GROUP_ID']
    if is_auth_group_id in group_uuids:
        return True
    return False


@save_antibody_blueprint.route('/antibodies-isauth', methods=['GET'])
def save_antibody_isauth():
    """
    Determine if the user can save AVR information. Used by the javascript code.
    """
    return make_response(jsonify({"authorized": save_antibody_isauth_check()}), 200)


@save_antibody_blueprint.route('/antibodies', methods=['POST'])
def save_antibody():
    if not save_antibody_isauth_check():
        abort(json_error('Not authorized to save antibody data', 401))
    # avr_pdf_uuid, and avr_pdf_filename are not required but are only present when a pdf is also uploaded.
    required_properties = (
        'uniprot_accession_number', 'hgnc_id', 'target_symbol', 'isotype', 'host',
        'clonality', 'clone_id', 'vendor', 'catalog_number', 'lot_number', 'recombinant',
        'rrid', 'method', 'tissue_preservation', 'protocol_doi', 'manuscript_doi', 'author_orcids',
        'organ', 'organ_uberon_id', 'avr_pdf_filename', 'cycle_number'
    )
    try:
        antibody = request.get_json()['antibody']
    except KeyError:
        abort(json_error('Antibody missing', 406))
    for prop in required_properties:
        if prop not in antibody:
            abort(json_error(
                'Antibody data incomplete: missing %s parameter' % prop, 400
                )
            )

    app = current_app
    cur = get_cursor(app)
    antibody['vendor_id'] = find_or_create_vendor(cur, antibody['vendor'])
    vendor = antibody['vendor']
    del antibody['vendor']
    antibody['antibody_uuid'] = get_hubmap_uuid(app.config['UUID_API_URL'])
    antibody['created_by_user_displayname'] = session['name']
    antibody['created_by_user_email'] = session['email']
    antibody['created_by_user_sub'] = session['sub']
    antibody['group_uuid'] = '7e5d3aec-8a99-4902-ab45-f2e3335de8b4'
    try:
        cur.execute(insert_query(), antibody)
        index_antibody(antibody | {'vendor': vendor})
    except UniqueViolation:
        abort(json_error('Antibody not unique', 400))
    return make_response(jsonify(id=cur.fetchone()[0], uuid=antibody['antibody_uuid']), 201)
