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
        'antibody_hubmap_id': antibody['antibody_hubmap_id'],
        'protocol_doi': antibody['protocol_doi'],
        'manuscript_doi': antibody['manuscript_doi'],
        'uniprot_accession_number': antibody['uniprot_accession_number'],
        'target_symbol': antibody['target_symbol'],
        'target_aliases': antibody['target_aliases'],
        'rrid': antibody['rrid'],
        'host': antibody['host'],
        'clonality': antibody['clonality'],
        'clone_id': antibody['clone_id'],
        'vendor_name': antibody['vendor_name'],
        'catalog_number': antibody['catalog_number'],
        'lot_number': antibody['lot_number'],
        'recombinant': antibody['recombinant'],
        'organ': antibody['organ'],
        'organ_uberon_id': antibody['organ_uberon_id'],
        'omap_id': antibody['omap_id'],
        'antigen_retrieval': antibody['antigen_retrieval'],
        'hgnc_id': antibody['hgnc_id'],
        'isotype': antibody['isotype'],
        'concentration_value': antibody['concentration_value'],
        'dilution_factor': antibody['dilution_factor'],
        'conjugate': antibody['conjugate'],
        'method': antibody['method'],
        'tissue_preservation': antibody['tissue_preservation'],
        'cycle_number': antibody['cycle_number'],
        'fluorescent_reporter': antibody['fluorescent_reporter'],
        'author_orcids': antibody['author_orcids'],
        'vendor_affiliation': antibody['vendor_affiliation'],
        'created_by_user_displayname': antibody['created_by_user_displayname'],
        'created_by_user_email': antibody['created_by_user_email'],
        'previous_version_id': antibody['previous_version_id'],
        'next_version_id': antibody['next_version_id'],
        'previous_version_pdf_uuid': antibody['previous_version_pdf_uuid'],
        'previous_version_pdf_filename': antibody['previous_version_pdf_filename']
    }
    if 'avr_pdf_uuid' in antibody and 'avr_pdf_filename' in antibody and antibody['avr_pdf_filename'] != '':
        doc['avr_pdf_uuid'] = antibody['avr_pdf_uuid']
        doc['avr_pdf_filename'] = antibody['avr_pdf_filename']
    logger.info(f"antibody: {antibody}")
    antibody_elasticsearch_index: str = current_app.config['ANTIBODY_ELASTICSEARCH_INDEX']
    es_conn.index(index=antibody_elasticsearch_index, body=doc) # pylint: disable=unexpected-keyword-arg, no-value-for-parameter


def update_next_version_es(antibody_hubmap_id: str, next_version_id: str):
    es_conn = elasticsearch.Elasticsearch([current_app.config['ELASTICSEARCH_SERVER']])
    antibody_elasticsearch_index = current_app.config['ANTIBODY_ELASTICSEARCH_INDEX']

    logger.info(f"*** Updating next_version_id for antibody_hubmap_id={antibody_hubmap_id} to {next_version_id}")

    try:
        search_result = es_conn.search(
            index=antibody_elasticsearch_index,
            body={
                "query": {
                    "term": {
                        "antibody_hubmap_id.keyword": antibody_hubmap_id
                    }
                },
                "_source": False 
            }
        )
        hits = search_result.get("hits", {}).get("hits", [])
        if not hits:
            logger.warning(f"No document found for antibody_hubmap_id={antibody_hubmap_id}")
            return

        doc_id = hits[0]["_id"]

        update_body = {
            'doc': {
                'next_version_id': next_version_id
            }
        }

        es_conn.update(
            index=antibody_elasticsearch_index,
            id=doc_id,
            body=update_body
        )

        logger.info(f"Successfully updated doc {doc_id} with next_version_id={next_version_id}")

    except Exception as e:
        logger.error(f"Failed to update next_version_id for {antibody_hubmap_id}: {str(e)}")


def execute_query_elasticsearch_directly(query):
    es_conn = elasticsearch.Elasticsearch([current_app.config['ELASTICSEARCH_SERVER']])

    # Return the elasticsearch resulting json data as json string
    antibody_elasticsearch_index: str = current_app.config['ANTIBODY_ELASTICSEARCH_INDEX']
    return es_conn.search(index=antibody_elasticsearch_index, body=query)


def execute_query_through_search_api(query):
    # SEARCHAPI_BASE_URL, and ANTIBODY_ELASTICSEARCH_INDEX should be defined in the Flask app.cfg file.
    # TODO: The reference to SEARCH_API_BASE in the config file seems to be breaking things?!
    searchapi_base_url: str = current_app.config['SEARCH_API_BASE'].rstrip("/")
    antibody_elasticsearch_index: str = current_app.config['ANTIBODY_ELASTICSEARCH_INDEX']
    # https://smart-api.info/ui/7aaf02b838022d564da776b03f357158#/search_by_index/search-post-by-index
    url: str = f"{searchapi_base_url}/{antibody_elasticsearch_index}/search"
    logger.info(f'execute_query_through_search_api() URL: {url}')
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
    #logger.info(f"execute_query: result = {result}")
    return result
