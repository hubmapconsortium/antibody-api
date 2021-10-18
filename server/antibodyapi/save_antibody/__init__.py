from flask import (
    abort, Blueprint, current_app, jsonify, make_response,
    redirect, render_template, request, session, url_for
)
from antibodyapi.utils import (
    allowed_file, base_antibody_query, find_or_create_vendor, get_cursor,
    get_file_uuid, get_hubmap_uuid, get_user_info, insert_query,
    insert_query_with_avr_file_and_uuid, json_error
)

save_antibody_blueprint = Blueprint('save_antibody', __name__)
@save_antibody_blueprint.route('/antibodies', methods=['POST'])
def save_antibody():
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
      'submitter_orciid'
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
    del antibody['vendor']
    antibody['antibody_uuid'] = get_hubmap_uuid(app.config['UUID_API_URL'])
    antibody['created_by_user_displayname'] = session['name']
    antibody['created_by_user_email'] = session['email']
    antibody['created_by_user_sub'] = session['sub']
    antibody['group_uuid'] = '7e5d3aec-8a99-4902-ab45-f2e3335de8b4'
    try:
        cur.execute(insert_query(), antibody)
    except UniqueViolation:
        abort(json_error('Antibody not unique', 400))
    return make_response(jsonify(id=cur.fetchone()[0], uuid=antibody['antibody_uuid']), 201)
