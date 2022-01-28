from flask import abort, Blueprint, current_app, jsonify, make_response, request, session
from psycopg2.errors import UniqueViolation #pylint: disable=no-name-in-module
from antibodyapi.utils import (
    find_or_create_vendor, base_antibody_query, base_antibody_query_result_to_json, get_cursor,
    get_hubmap_uuid, insert_query, json_error
)
from antibodyapi.utils.elasticsearch import index_antibody
import elasticsearch


restore_elasticsearch_blueprint = Blueprint('restore_elasticsearch', __name__)
@restore_elasticsearch_blueprint.route('/restore_elasticsearch', methods=['PUT'])
def restore_elasticsearch():
    # Delete the index...
    server: str = current_app.config['ELASTICSEARCH_SERVER']
    es_conn = elasticsearch.Elasticsearch([server])
    antibody_elasticsearch_index: str = current_app.config['ANTIBODY_ELASTICSEARCH_INDEX']
    print(f'Restoring Elastic Search index {antibody_elasticsearch_index} on server {server}')
    es_conn.indices.delete(index=antibody_elasticsearch_index, ignore=[400, 404])

    cur = get_cursor(current_app)
    cur.execute(base_antibody_query() + ' ORDER BY a.id ASC')
    print(f'Rows retrieved: {cur.rowcount}')
    results = []
    for antibody_array in cur:
        antibody: dict = base_antibody_query_result_to_json(antibody_array)
        index_antibody(antibody)
    return make_response(jsonify(antibodies=results), 200)
