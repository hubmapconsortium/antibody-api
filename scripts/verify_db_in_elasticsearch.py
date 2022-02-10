#!/usr/bin/env python

# Directions:
# Upload the .csv and correcponding .pdf file through the UI at localhost:500
# python3 -m pip install --upgrade pip
# python3 -m venv venv
# source venv/bin/activate
# pip install -r ../requirements.txt
# pip install psycopg2 elasticsearch requests
# ./verify_db_in_elasticsearch.py

import argparse, csv, sys, psycopg2, elasticsearch, json, requests, io, PyPDF2
from urllib.parse import urlparse
from enum import IntEnum, unique


class RawTextArgumentDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter
):
    pass


# https://docs.python.org/3/howto/argparse.html
parser = argparse.ArgumentParser(
    description='''
    Determine that the records in the PosgreSQL database are represented in ElasticSearch, and Assets.

    You should make sure that the URLs below match the environment that you did the upload on.
    To do this check the instance/app.conf file on the Antibody Server that you are accessing.
    The POSTGRES_URL maps to the DATABASE_HOST, DATABASE_NAME, DATABASE_USER, and DATABASE_PASSWORD in the .conf file.
    The ELASTICSEARCH_URL maps to the ELASTICSEARCH_SERVER in the .conf file.
    ''',
    formatter_class=RawTextArgumentDefaultsHelpFormatter)
parser.add_argument("-e", '--elasticsearch_url', type=str, default='http://localhost:9200',
                    help='the ElasticSearch server url')
parser.add_argument("-i", '--elasticsearch_index', type=str, default='hm_antibodies',
                    help='the ElasticSearch index')
parser.add_argument("-p", '--postgresql_url', type=str, default='http://postgres:password@localhost:5432/antibodydb',
                    help='the PostgreSQL database url')
parser.add_argument("-a", '--assets_url', type=str, default='https://assets.test.hubmapconsortium.org',
                    help='the Assets Server to check for the .pdf file if any')
parser.add_argument("-v", "--verbose", action="store_true",
                    help='verbose output')

args = parser.parse_args()


def vprint(*pargs, **pkwargs) -> None:
    if args.verbose is True:
        print(*pargs, file=sys.stderr, **pkwargs)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def make_db_connection(postgresql_url: str):
    url = urlparse(postgresql_url)
    return psycopg2.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        dbname=url.path[1:]
    )


@unique
class SI(IntEnum):
    ANTIBODY_UUID = 0
    AVR_FILENAME = 1
    AVR_UUID = 2
    PROTOCOLS_IO_DOI = 3
    UNIPROT_ACCESSION_NUMBER = 4
    TARGET_NAME = 5
    RRID = 6
    ANTIBODY_NAME = 7
    HOST_ORGANISM = 8
    CLONALITY = 9
    VENDOR_NAME = 10
    CATALOG_NUMBER = 11
    LOT_NUMBER = 12
    RECOMBINATE = 13
    ORGAN_OR_TISSSUE = 14
    HUBMAP_PLATFORM = 15
    SUBMITTER_ORCIID = 16
    CREATED_TIMESTAMP = 17
    CREATED_BY_USER_DISPLAYNAME = 18
    CREATED_BY_USER_EMAIL = 19
    CREATED_BY_USER_SUB = 20
    GROUP_UUID = 21


QUERY = '''
SELECT
    a.antibody_uuid,
    a.avr_filename, a.avr_uuid,
    a.protocols_io_doi,
    a.uniprot_accession_number,
    a.target_name, a.rrid,
    a.antibody_name, a.host_organism,
    a.clonality, v.name,
    a.catalog_number, a.lot_number,
    a.recombinant, a.organ_or_tissue,
    a.hubmap_platform, a.submitter_orciid,
    a.created_timestamp,
    a.created_by_user_displayname, a.created_by_user_email,
    a.created_by_user_sub, a.group_uuid
FROM antibodies a
JOIN vendors v ON a.vendor_id = v.id
'''


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


def check_hit(es_hit: dict, ds_key: str, db_row, db_row_index: int, antibody_uuid: str) -> None:
    if ds_key not in es_hit:
        eprint(f"ERROR: Key {ds_key} not in ElasticSearch hit for antibody_uuid '{antibody_uuid}")
        return
    if len(db_row) < db_row_index:
        eprint(f"ERROR: Insufficient entrys in database record for ElasticSearch {ds_key} for antibody_uuid '{antibody_uuid}")
        return
    if ds_key == 'recombinant' and map_string_to_bool(es_hit[ds_key]) != db_row[db_row_index]:
        eprint(f"ERROR: ElasticSearch hit key '{ds_key}' value '{es_hit[ds_key]}' does not match expected PostgreSQL entry '{db_row[db_row_index]}' for antibody_uuid '{antibody_uuid}")
    elif ds_key != 'recombinant' and es_hit[ds_key] != db_row[db_row_index]:
        eprint(f"ERROR: xxxElasticSearch hit key '{ds_key}' value '{es_hit[ds_key]}' does not match expected PostgreSQL entry '{db_row[db_row_index]}' for antibody_uuid '{antibody_uuid}")


def check_es_entry_to_db_row(es_conn, db_row) -> None:
    antibody_uuid: str = db_row[SI.ANTIBODY_UUID].replace('-', '')
    query: dict = json.loads('{"match": {"antibody_uuid": "%s"}}' % antibody_uuid)
    es_resp = es_conn.search(index=args.elasticsearch_index, query=query)
    if es_resp['hits']['total']['value'] == 0:
        eprint(f"ERROR: ElasticSearch query: {query}; no rows found")
    if es_resp['hits']['total']['value'] > 1:
        eprint(f"ERROR: ElasticSearch query: {query}; multiple rows found")
    source: dict = es_resp['hits']['hits'][0]['_source']
    check_hit(source, 'protocols_io_doi', db_row, SI.PROTOCOLS_IO_DOI, antibody_uuid)
    check_hit(source, 'uniprot_accession_number', db_row, SI.UNIPROT_ACCESSION_NUMBER, antibody_uuid)
    check_hit(source, 'target_name', db_row, SI.TARGET_NAME, antibody_uuid)
    check_hit(source, 'rrid', db_row, SI.RRID, antibody_uuid)
    check_hit(source, 'antibody_name', db_row, SI.ANTIBODY_NAME, antibody_uuid)
    check_hit(source, 'host_organism', db_row, SI.HOST_ORGANISM, antibody_uuid)
    check_hit(source, 'clonality', db_row, SI.CLONALITY, antibody_uuid)
    check_hit(source, 'vendor', db_row, SI.VENDOR_NAME, antibody_uuid)
    check_hit(source, 'catalog_number', db_row, SI.CATALOG_NUMBER, antibody_uuid)
    check_hit(source, 'lot_number', db_row, SI.LOT_NUMBER, antibody_uuid)
    check_hit(source, 'recombinant', db_row, SI.RECOMBINATE, antibody_uuid)
    check_hit(source, 'organ_or_tissue', db_row, SI.ORGAN_OR_TISSSUE, antibody_uuid)
    check_hit(source, 'hubmap_platform', db_row, SI.HUBMAP_PLATFORM, antibody_uuid)
    check_hit(source, 'submitter_orciid', db_row, SI.SUBMITTER_ORCIID, antibody_uuid)


# If you uploaded the file on DEV, then the URL:
# https://assets.dev.hubmapconsortium.org/<uuid>/<relative-file-path>
# will download that file. The file assets service is not an API, but the Gateway handles the auth check
# before you can access that file. It's really direct access to the file system through the <relative-file-path>.
# The gateway file_auth checks on that <uuid> and queries the permission along with the users token to determine
# if the user has access to the file.
def check_pdf_file_upload(avr_uuid: str, avr_filename: str):
    url: str = f"{args.assets_url}/{avr_uuid.replace('-', '')}/{avr_filename}"
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
        eprint(f"ERROR: avr_file {avr_filename} found, but not a valid .pdf file")
        return
    vprint(f" valid .pdf file")


db_conn = None
cursor = None
try:
    db_conn = make_db_connection(args.postgresql_url)
    vprint(f"Connected to database at URL '{args.postgresql_url}'")
    cursor = db_conn.cursor()
except psycopg2.Error as e:
    eprint(f"ERROR: Unable to connect to database at URL '{args.postgresql_url}'")
    exit(1)

es_conn = None
try:
    es_conn = elasticsearch.Elasticsearch([args.elasticsearch_url])
    vprint(f"Connected to ElasticSearch at URL '{args.elasticsearch_url}'")
except elasticsearch.ElasticsearchException as e:
    eprint(f"ERROR: Unable to connect to ElasticSearch at URL '{args.elasticsearch_url}': {e}")
    exit(1)

try:
    cursor.execute(QUERY)
    rows_processed = 0
    for db_row in cursor.fetchall():
        check_es_entry_to_db_row(es_conn, db_row)
        avr_filename = db_row[SI.AVR_FILENAME]
        if avr_filename is not None:
            check_pdf_file_upload(db_row[SI.AVR_UUID], avr_filename)
        rows_processed = rows_processed + 1
    eprint(f"Database Rows processed: {rows_processed}")

except psycopg2.Error as e:
    eprint(f"ERROR: Accessing database at {args.postgresql_url}: {e.pgerror}")
except elasticsearch.ElasticsearchException as e:
    eprint(f"ERROR: Accessing ElasticSearch at URL '{args.elasticsearch_url}': {e}")
finally:
    if db_conn:
        cursor.close()
        db_conn.close()
        vprint(f"Closed connected to database at URL '{args.postgresql_url}'")

vprint("Done.")
