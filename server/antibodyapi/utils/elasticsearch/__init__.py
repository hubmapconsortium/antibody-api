import elasticsearch
from flask import current_app
import requests
import logging

# TODO: Joe 12/1/21
# - Rename the configuration name (line 8) 'ELASTICSEARCH_SERVER' to 'SEARCH_API_URL' to hit the search API server
# - Have to manually create the 'hm_antibodies' index into Elastic Search and make come configuration change into
#   search api so that it supports this index.
# - Import the data associated with the index though some script.
# - He is using the elastic search methods against the elastic search server we can get rid of the Elastic Search
#   dependency, or move the dependency to the script so that we can import data using the functionality there.
#   Better yet, use the Neo4j Admin import to load the data into the index.
# Search UI https://antibody-api.dev.hubmapconsortium.org/

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
        'submitter_orciid': antibody['submitter_orciid']
    }
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
    response = requests.post(url, header="{'Content-Type': 'application/json'}", data=query)

    if response.status_code != 200:
        logger.error(f"The search-api has returned status_code {response.status_code}: {response.text}")
        raise requests.exceptions.RequestException(response.text)

    return response.json()


def execute_query(query):
    logger.info(f"*** Elastic Search Query: {query}")
    return execute_query_elasticsearch_directly(query)
