import elasticsearch
from flask import current_app
import requests
import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def index_antibody(antibody: dict):
    """
    This will save the antibody information to Elastic Search.

    It should be called within the code for the endpoint at server.save_antibody(),
    and server.import_antibodies() after the antibody information is successfully saved
    to the PostgreSQL database.
    """
    es_conn = elasticsearch.Elasticsearch([current_app.config['ELASTICSEARCH_SERVER']])
    logger.info(f"*** Indexing: {antibody}")
    doc = {
        'antibody_uuid': antibody['antibody_uuid'],
        'protocol_doi': antibody['protocol_doi'],
        'manuscript_doi': antibody['manuscript_doi'],
        'uniprot_accession_number': antibody['uniprot_accession_number'],
        'target_symbol': antibody['target_symbol'],
        'target_aliases': antibody['target_aliases'],
        'rrid': antibody['rrid'],
        'host': antibody['host'],
        'clonality': antibody['clonality'],
        'vendor_name': antibody['vendor'],
        'catalog_number': antibody['catalog_number'],
        'lot_number': antibody['lot_number'],
        'recombinant': antibody['recombinant'],
        'organ': antibody['organ'],
        'organ_uberon': antibody['organ_uberon'],
        'omap_id': antibody['omap_id'],
        'antigen_retrieval': antibody['antigen_retrieval'],
        'hgnc_id': antibody['hgnc_id'],
        'isotype': antibody['isotype'],
        'concentration_value': antibody['concentration_value'],
        'dilution': antibody['dilution'],
        'conjugate': antibody['conjugate'],
        'method': antibody['method'],
        'tissue_preservation': antibody['tissue_preservation'],
        'cycle_number': antibody['cycle_number'],
        'fluorescent_reporter': antibody['fluorescent_reporter'],
        'author_orcids': antibody['author_orcids'],
        'vendor_affiliation': antibody['vendor_affiliation'],
        'created_by_user_displayname': antibody['created_by_user_displayname'],
        'created_by_user_email': antibody['created_by_user_email']
    }
    if 'avr_pdf_uuid' in antibody and 'avr_pdf_filename' in antibody and antibody['avr_pdf_filename'] != '':
        doc['avr_pdf_uuid'] = antibody['avr_pdf_uuid']
        doc['avr_pdf_filename'] = antibody['avr_pdf_filename']
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
    logger.debug(f'execute_query_through_search_api() URL: {url}')
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
