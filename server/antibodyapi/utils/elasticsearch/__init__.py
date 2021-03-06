import elasticsearch
from flask import current_app
import requests
import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


# This is called within the code for the endpoint at "server.save_antibody()", and "server.import_antibodies()"
# after the antibody information is successfully saved to the PostgreSQL database.
def index_antibody(antibody: dict):
    es_conn = elasticsearch.Elasticsearch([current_app.config['ELASTICSEARCH_SERVER']])
    logger.info(f"*** Indexing: {antibody}")
    doc = {
        'antibody_uuid': antibody['antibody_uuid'],
        'protocols_io_doi': antibody['protocols_io_doi'],
        'uniprot_accession_number': antibody['uniprot_accession_number'],
        'target_name': antibody['target_name'],
        'rrid': antibody['rrid'],
        'antibody_name': antibody['antibody_name'],
        'host_organism': antibody['host_organism'],
        'clonality': antibody['clonality'],
        'vendor': antibody['vendor'],
        'catalog_number': antibody['catalog_number'],
        'lot_number': antibody['lot_number'],
        'recombinant': antibody['recombinant'],
        'organ_or_tissue': antibody['organ_or_tissue'],
        'hubmap_platform': antibody['hubmap_platform'],
        'submitter_orcid': antibody['submitter_orcid'],
        'created_by_user_email': antibody['created_by_user_email']
    }
    if 'avr_uuid' in antibody and 'avr_filename' in antibody and antibody['avr_filename'] != '':
        doc['avr_uuid'] = antibody['avr_uuid']
        doc['avr_filename'] = antibody['avr_filename']
    antibody_elasticsearch_index: str = current_app.config['ANTIBODY_ELASTICSEARCH_INDEX']
    es_conn.index(index=antibody_elasticsearch_index, body=doc) # pylint: disable=unexpected-keyword-arg, no-value-for-parameter


def execute_query_elasticsearch_directly(query):
    es_conn = elasticsearch.Elasticsearch([current_app.config['ELASTICSEARCH_SERVER']])

    # Return the elasticsearch resulting json data as json string
    antibody_elasticsearch_index: str = current_app.config['ANTIBODY_ELASTICSEARCH_INDEX']
    return es_conn.search(index=antibody_elasticsearch_index, body=query)


def execute_query_through_search_api(query):
    # SEARCHAPI_BASE_URL, and ANTIBODY_ELASTICSEARCH_INDEX should be defined in the Flask app.cfg file.
    searchapi_base_url: str = current_app.config['SEARCH_API_BASE'].rstrip("/")
    antibody_elasticsearch_index: str = current_app.config['ANTIBODY_ELASTICSEARCH_INDEX']
    # https://smart-api.info/ui/7aaf02b838022d564da776b03f357158#/search_by_index/search-post-by-index
    url: str = f"{searchapi_base_url}/{antibody_elasticsearch_index}/search"
    response = requests.post(url, headers={"Content-Type": "application/json"}, json=query)

    if response.status_code != 200:
        logger.error(f"The search-api has returned status_code {response.status_code}: {response.text}")
        raise requests.exceptions.RequestException(response.text)

    return response.json()


def execute_query(query):
    logger.debug(f"*** Elastic Search Query: {query}")
    query_directly: str = current_app.config['QUERY_ELASTICSEARCH_DIRECTLY']
    result: dict = {}
    if query_directly is True:
        result = execute_query_elasticsearch_directly(query)
    result = execute_query_through_search_api(query)
    logger.info(f"execute_query: result = {result}")
    return result
