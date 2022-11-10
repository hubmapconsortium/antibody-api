from flask import abort, Blueprint, current_app, jsonify, make_response, request, session
from psycopg2.errors import UniqueViolation #pylint: disable=no-name-in-module
from antibodyapi.utils import (
    find_or_create_vendor, get_cursor,
    get_hubmap_uuid, insert_query, json_error
)
from antibodyapi.utils.elasticsearch import index_antibody

save_antibody_blueprint = Blueprint('save_antibody', __name__)


@save_antibody_blueprint.route('/antibodies', methods=['POST'])
def save_antibody():
    # avr_uuid, and avr_filename are not required but are only present when a pdf is also uploaded.
    required_properties = (
      'protocols_io_doi',
      'uniprot_accession_number',
      'target_name',
      'rrid',
      'antibody_name',
      'host_organism',
      'clonality',
      'vendor',
      'catalog_number',
      'lot_number',
      'recombinant',
      'organ_or_tissue',
      'hubmap_platform',
      'submitter_orcid'
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
