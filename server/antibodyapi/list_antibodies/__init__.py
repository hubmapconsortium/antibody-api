from flask import (
    Blueprint, current_app, jsonify, make_response,
    redirect, render_template, session, url_for
)
from antibodyapi.utils import (
    allowed_file, base_antibody_query, find_or_create_vendor, get_cursor,
    get_file_uuid, get_hubmap_uuid, get_user_info, insert_query,
    insert_query_with_avr_file_and_uuid, json_error
)

list_antibodies_blueprint = Blueprint('list_antibodies', __name__)
@list_antibodies_blueprint.route('/antibodies')
def list_antibodies():
    cur = get_cursor(current_app)
    cur.execute(base_antibody_query() + ' ORDER BY a.id ASC')
    results = []
    for antibody in cur:
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
            'created_by_user_displayname': antibody[15],
            'created_by_user_email': antibody[16],
            'created_by_user_sub': antibody[17],
            'group_uuid': antibody[18]
        }
        results.append(ant)
    return make_response(jsonify(antibodies=results), 200)
