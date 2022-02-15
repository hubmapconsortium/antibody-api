#!/usr/bin/env python

# Directions:
# python3 -m pip install --upgrade pip
# python3 -m venv venv; source venv/bin/activate
# pip install -r ../requirements.txt
# ./verify_db_in_elasticsearch.py

import argparse
import elasticsearch
from utils import *


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
parser.add_argument("-e", '--elasticsearch_url', type=str, default='http://localhost',
                    help='the ElasticSearch server url')
parser.add_argument("-i", '--elasticsearch_index', type=str, default='hm_antibodies',
                    help='the ElasticSearch index')
parser.add_argument("-p", '--postgresql_url', type=str, default='http://postgres:password@localhost/antibodydb',
                    help='the PostgreSQL database url. Some characters in the password may need to be urlencoded')
parser.add_argument("-a", '--assets_url', type=str, default='https://assets.test.hubmapconsortium.org',
                    help='the Assets Server to check for the .pdf file if any')
parser.add_argument("-v", "--verbose", action="store_true",
                    help='verbose output')

args = parser.parse_args()
os.environ['VERBOSE'] = str(args.verbose)


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
    es_conn = make_es_connection(args.elasticsearch_url)
except elasticsearch.ElasticsearchException as e:
    eprint(f"ERROR: Unable to connect to ElasticSearch at URL '{args.elasticsearch_url}': {e}")
    exit(1)

try:
    cursor.execute(QUERY)
    vprint(f"Executed PostgreSQL query")
    rows_processed = 0
    for db_row in cursor.fetchall():
        check_es_entry_to_db_row(es_conn, args.elasticsearch_index, db_row)
        avr_filename = db_row[SI.AVR_FILENAME]
        if avr_filename is not None:
            check_pdf_file_upload(args.assets_url, db_row[SI.AVR_UUID], avr_filename)
        rows_processed = rows_processed + 1
    eprint(f"Database Rows processed: {rows_processed}")

except psycopg2.Error as e:
    eprint(f"ERROR: Accessing database at {args.postgresql_url}: {e.pgerror}")
except elasticsearch.TransportError as e:
    eprint(f"ERROR: Querying ElasticSearch at URL '{args.elasticsearch_url}': {e}")
except elasticsearch.ElasticsearchException as e:
    eprint(f"ERROR: Accessing ElasticSearch at URL '{args.elasticsearch_url}': {e}")
finally:
    if db_conn:
        cursor.close()
        db_conn.close()
        vprint(f"Closed connected to database at URL '{args.postgresql_url}'")

eprint("Done.")
