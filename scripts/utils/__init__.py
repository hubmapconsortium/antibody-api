# These are common to the 'verify_*.py' scripts.

import psycopg2
import os
import sys
import json
import requests
import PyPDF2
import io
import elasticsearch
from urllib.parse import urlparse, unquote
from enum import IntEnum, unique


def vprint(*pargs, **pkwargs) -> None:
    if 'VERBOSE' in os.environ and os.environ['VERBOSE'] == 'True':
        print(*pargs, file=sys.stderr, **pkwargs)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def make_db_connection(postgresql_url: str):
    url = urlparse(postgresql_url)
    port: int = 5432
    if url.port is not None:
        port = url.port
    vprint(f"make_db_connection user:{url.username}, password:{unquote(url.password)}, host:{url.hostname}, port:{port}, dbname:{url.path[1:]}")
    return psycopg2.connect(
        user=url.username,
        password=unquote(url.password),
        host=url.hostname,
        port=port,
        dbname=url.path[1:]
    )


def make_es_connection(es_url: str):
    url = urlparse(es_url)
    vprint(f"Connecting to ElasticSearch at URL '{url.geturl()}'")
    es_conn = elasticsearch.Elasticsearch(url.geturl(), timeout=30)
    return es_conn


@unique
class SI(IntEnum):
    ANTIBODY_UUID = 0
    AVR_PDF_FILENAME = 1
    AVR_PDF_UUID = 2
    PROTOCOLS_DOI = 3
    UNIPROT_ACCESSION_NUMBER = 4
    TARGET_SYMBOL = 5
    RRID = 6
    HOST = 7
    CLONALITY = 8
    VENDOR_NAME = 9
    CATALOG_NUMBER = 10
    LOT_NUMBER = 11
    RECOMBINANT = 12
    ORGAN = 13
    METHOD = 14
    AUTHOR_ORCIDS = 15
    HGNC_ID = 16
    ISOTYPE = 17
    CONCENTRATION_VALUE = 18
    DILUTION = 19
    CONJUGATE = 20
    TISSUE_PRESERVATION = 21
    CYCLE_NUMBER = 22
    FLUORESCENT_REPORTER = 23
    MANUSCRIPT_DOI = 24
    VENDOR_AFFILIATION = 25
    ORGAN_UBERON = 26
    ANTIGEN_RETRIEVAL = 27
    OMAP_ID = 28
    CREATED_TIMESTAMP = 29
    CREATED_BY_USER_DISPLAYNAME = 30
    CREATED_BY_USER_EMAIL = 31
    CREATED_BY_USER_SUB = 32
    GROUP_UUID = 33


QUERY = '''
SELECT
    a.antibody_uuid,
    a.avr_pdf_filename, a.avr_pdf_uuid,
    a.protocols_doi, a.uniprot_accession_number,
    a.target_symbol, a.rrid, a.host, a.clonality, v.vendor_name,
    a.catalog_number, a.lot_number, a.recombinant, a.organ,
    a.method, a.author_orcids, a.hgnc_id, a.isotype,
    a.concentration_value, a.dilution, a.conjugate,
    a.tissue_preservation, a.cycle_number, a.fluorescent_reporter,
    a.manuscript_doi, a.vendor_affiliation, a.organ_uberon,
    a.antigen_retrieval, a.omap_id,
    a.created_timestamp,
    a.created_by_user_displayname, a.created_by_user_email,
    a.created_by_user_sub, a.group_uuid
FROM antibodies a
JOIN vendors v ON a.vendor_id = v.id
'''


def where_condition(csv_row: dict, column: str, condition: str = 'AND') -> str:
    column_name: str = column.split('.')[1]
    value: str = csv_row[column_name]
    return f" {condition} {column} LIKE '{value}'"


def base_antibody_query(csv_row: dict):
    return QUERY + 'WHERE' + where_condition(csv_row, 'a.protocols_doi', '') + \
            where_condition(csv_row, 'a.uniprot_accession_number') + \
            where_condition(csv_row, 'a.target_symbol') + where_condition(csv_row, 'a.rrid') + \
            where_condition(csv_row, 'a.catalog_number') + where_condition(csv_row, 'a.lot_number') + \
            where_condition(csv_row, 'a.organ') + where_condition(csv_row, 'a.author_orcids')


def map_string_to_bool(value: str):
    if value.upper() == 'TRUE' or value.upper() == 'YES':
        return True
    elif value.upper() == 'FALSE' or value.upper() == 'NO':
        return False
    return value


def map_empty_string_to_none(value: str):
    if value == '':
        return None
    return value


def check_hit_not_match_error(es_hit: dict, ds_key: str, db_row, db_row_index: int, antibody_uuid: str) -> None:
    eprint(f"ERROR: ElasticSearch hit key '{ds_key}' value '{es_hit[ds_key]}' does not match expected PostgreSQL entry '{db_row[db_row_index]}' for antibody_uuid '{antibody_uuid}")


def check_hit(es_hit: dict, ds_key: str, db_row, db_row_index: int, antibody_uuid: str) -> None:
    if ds_key not in es_hit:
        eprint(f"ERROR: Key '{ds_key}' not in ElasticSearch hit for antibody_uuid '{antibody_uuid}'")
        return
    if len(db_row) < db_row_index:
        eprint(f"ERROR: Insufficient entries in database record for ElasticSearch '{ds_key}' for antibody_uuid '{antibody_uuid}'")
        return
    if ds_key == 'recombinant':
        if es_hit[ds_key] != db_row[db_row_index]:
            check_hit_not_match_error(es_hit, ds_key, db_row, db_row_index, antibody_uuid)
    elif ds_key == 'vendor':
        if map_string_to_bool(es_hit[ds_key]).upper() != db_row[db_row_index].upper():
            check_hit_not_match_error(es_hit, ds_key, db_row, db_row_index, antibody_uuid)
    elif ds_key == 'avr_pdf_uuid':
        if es_hit[ds_key] != db_row[db_row_index].replace('-', ''):
            check_hit_not_match_error(es_hit, ds_key, db_row, db_row_index, antibody_uuid)
    else:
        if es_hit[ds_key] != db_row[db_row_index]:
            check_hit_not_match_error(es_hit, ds_key, db_row, db_row_index, antibody_uuid)


# This should check_hit on every item listed in:
# 'server/antibodyapi/utils/elasticsearch/__init__.py: index_antibody(() doc
def check_es_entry_to_db_row(es_conn, es_index, db_row) -> None:
    antibody_uuid: str = db_row[SI.ANTIBODY_UUID].replace('-', '')
    es_query: dict = json.loads('{"query": {"match": {"antibody_uuid": "%s"}}}' % antibody_uuid)
    vprint(f"Executing ElasticSearch query: {es_query}")
    es_resp = es_conn.search(index=es_index, body=es_query)
    vprint(f"ElasticSearch query response: {es_resp}")
    if es_resp['hits']['total']['value'] == 0:
        eprint(f"ERROR: ElasticSearch query: {es_query}; no rows found")
    if es_resp['hits']['total']['value'] > 1:
        eprint(f"ERROR: ElasticSearch query: {es_query}; multiple rows found")
    hits = es_resp['hits']['hits']
    if len(hits) == 0:
        eprint(f"ERROR: ElasticSearch query: {es_query}; returned no hits {hits}")
        return
    source: dict = hits[0]['_source']
    if 'avr_pdf_uuid' in source:
        check_hit(source, 'avr_pdf_filename', db_row, SI.AVR_PDF_FILENAME, antibody_uuid)
        check_hit(source, 'avr_pdf_uuid', db_row, SI.AVR_PDF_UUID, antibody_uuid)
    check_hit(source, 'protocols_doi', db_row, SI.PROTOCOLS_IO_DOI, antibody_uuid)
    check_hit(source, 'uniprot_accession_number', db_row, SI.UNIPROT_ACCESSION_NUMBER, antibody_uuid)
    check_hit(source, 'target_symbol', db_row, SI.TARGET_SYMBOL, antibody_uuid)
    check_hit(source, 'rrid', db_row, SI.RRID, antibody_uuid)
    check_hit(source, 'host', db_row, SI.HOST, antibody_uuid)
    check_hit(source, 'clonality', db_row, SI.CLONALITY, antibody_uuid)
    check_hit(source, 'vendor_name', db_row, SI.VENDOR_NAME, antibody_uuid)
    check_hit(source, 'catalog_number', db_row, SI.CATALOG_NUMBER, antibody_uuid)
    check_hit(source, 'lot_number', db_row, SI.LOT_NUMBER, antibody_uuid)
    check_hit(source, 'recombinant', db_row, SI.RECOMBINANT, antibody_uuid)
    check_hit(source, 'organ', db_row, SI.ORGAN, antibody_uuid)

    check_hit(source, 'method', db_row, SI.METHOD, antibody_uuid)
    check_hit(source, 'author_orcids', db_row, SI.AUTHOR_ORCIDS, antibody_uuid)
    check_hit(source, 'hgnc_id', db_row, SI.HGNC_ID, antibody_uuid)
    check_hit(source, 'concentration_value', db_row, SI.CONCENTRATION_VALUE, antibody_uuid)
    check_hit(source, 'dilution', db_row, SI.DILUTION, antibody_uuid)
    check_hit(source, 'conjugate', db_row, SI.CONJUGATE, antibody_uuid)
    check_hit(source, 'tissue_preservation', db_row, SI.TISSUE_PRESERVATION, antibody_uuid)
    check_hit(source, 'cycle_number', db_row, SI.CYCLE_NUMBER, antibody_uuid)
    check_hit(source, 'fluorescent_reporter', db_row, SI.FLUORESCENT_REPORTER, antibody_uuid)
    check_hit(source, 'manuscript_doi', db_row, SI.MANUSCRIPT_DOI, antibody_uuid)
    check_hit(source, 'vendor_affiliation', db_row, SI.VENDOR_AFFILIATION, antibody_uuid)
    check_hit(source, 'organ_uberon', db_row, SI.ORGAN_UBERON, antibody_uuid)
    check_hit(source, 'antigen_retrieval', db_row, SI.ANTIGEN_RETRIEVAL, antibody_uuid)
    check_hit(source, 'omap_id', db_row, SI.OMAP_ID, antibody_uuid)
    check_hit(source, 'created_timestamp', db_row, SI.CREATED_TIMESTAMP, antibody_uuid)
    check_hit(source, 'created_by_user_displayname', db_row, SI.CREATED_BY_USER_DISPLAYNAME, antibody_uuid)

    check_hit(source, 'created_by_user_email', db_row, SI.CREATED_BY_USER_EMAIL, antibody_uuid)


# If you uploaded the file on DEV, then the URL:
# https://assets.dev.hubmapconsortium.org/<uuid>/<relative-file-path>
# will download that file. The file assets service is not an API, but the Gateway handles the auth check
# before you can access that file. It's really direct access to the file system through the <relative-file-path>.
# The gateway file_auth checks on that <uuid> and queries the permission along with the users token to determine
# if the user has access to the file.
def check_pdf_file_upload(assets_url: str, avr_pdf_uuid: str, avr_pdf_filename: str):
    url: str = f"{assets_url}/{avr_pdf_uuid.replace('-', '')}/{avr_pdf_filename}"
    vprint(f"Checking for avr_file with request {url}", end='')
    response: requests.Response = requests.get(url)
    if response.status_code != 200:
        eprint(f"ERROR: avr_file not found. The request '{url} returns status_code {response.status_code}")
        return
    content: bytes = response.content
    try:
        PyPDF2.PdfFileReader(stream=io.BytesIO(content))
    except PyPDF2.utils.PdfReadError:
        vprint(f" INVALID .pdf file")
        eprint(f"ERROR: avr_file {avr_pdf_filename} found, but not a valid .pdf file")
        return
    vprint(f" valid .pdf file")
