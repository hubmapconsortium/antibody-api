from flask import Blueprint, current_app, jsonify, make_response
from antibodyapi.utils import base_antibody_query, base_antibody_query_result_to_json, get_cursor

list_antibodies_blueprint = Blueprint('list_antibodies', __name__)


@list_antibodies_blueprint.route('/antibodies')
def list_antibodies():
    cur = get_cursor(current_app)
    cur.execute(base_antibody_query() + ' ORDER BY a.id ASC')
    results = []
    for antibody in cur:
        ant = base_antibody_query_result_to_json(antibody)
        results.append(ant)
    return make_response(jsonify(antibodies=results), 200)
