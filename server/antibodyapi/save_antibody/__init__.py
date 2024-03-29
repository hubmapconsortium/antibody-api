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
    vendor_name = antibody['vendor']
    del antibody['vendor']
    hubmap_uuid_dict: dict = get_hubmap_uuid(app.config['UUID_API_URL'])
    antibody['antibody_uuid'] = hubmap_uuid_dict.get('uuid')
    antibody['antibody_hubmap_id'] = hubmap_uuid_dict.get('hubmap_id')
    antibody['created_by_user_displayname'] = session['name']
    antibody['created_by_user_email'] = session['email']
    antibody['created_by_user_sub'] = session['sub']
    antibody['group_uuid'] = '7e5d3aec-8a99-4902-ab45-f2e3335de8b4'
    try:
        cur.execute(insert_query(), antibody)
        index_antibody(antibody | {'vendor_name': vendor_name})
    except UniqueViolation:
        abort(json_error('Antibody not unique', 400))
    return make_response(jsonify(id=cur.fetchone()[0], uuid=antibody['antibody_uuid']), 201)
