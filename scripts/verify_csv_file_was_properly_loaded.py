#!/usr/bin/env python

# Directions:
# Upload the .csv and correcponding .pdf file through the UI at localhost:500
# python3 -m pip install --upgrade pip
# python3 -m venv venv
# source venv/bin/activate
# pip install -r ../requirements.txt
# ./verify_csv_file_was_properly_loaded.py ../server/manual_test_files/upload_mulriple_with_pdf/antibodies.csv

import argparse
import csv
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
    Determine if data in the .csv file is present in PosgreSQL, ElasticSearch, and Assets.
    
    You will first upload the .csv and associated .pdf file using the UPLOAD button on the search bar
    of the Antibody GUI.
    
    You should make sure that the URLs below match the environment that you did the upload on.
    To do this check the instance/app.conf file on the Antibody Server that you are accessing.
    The POSTGRES_URL maps to the DATABASE_HOST, DATABASE_NAME, DATABASE_USER, and DATABASE_PASSWORD in the .conf file.
    The ELASTICSEARCH_URL maps to the ELASTICSEARCH_SERVER in the .conf file.
    ''',
    formatter_class=RawTextArgumentDefaultsHelpFormatter)
parser.add_argument('csv_file',
                    help='the .csv file used in the upload which may contain references to a .pdf file')
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
os.environ['VERBOSE'] = str(args.verbose)

CSV_ROWS = 19
ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Here we only need to check those entries not used i the where clause of the query
def check_csv_row_to_db_row(csv_row, db_row) -> None:
    if csv_row['clonality'] != db_row[SI.CLONALITY]:
        eprint(
            f"ERROR: In file row {csv_row_number}; 'clonality' in .csv file is '{csv_row['clonality']}', but '{db_row[SI.CLONALITY]}' in database")
    if map_string_to_bool(csv_row['recombinant']) != db_row[SI.RECOMBINATE]:
        eprint(
            f"ERROR: In file row {csv_row_number}; 'recombinant' in .csv file is '{csv_row['recombinant']}', but '{db_row[SI.RECOMBINATE]}' in database")
    if 'avr_filename' in csv_row and map_empty_string_to_none(csv_row['avr_filename']) != db_row[SI.AVR_FILENAME]:
        eprint(
            f"ERROR: In file row {csv_row_number}; 'avr_filename' in .csv file is '{csv_row['avr_filename']}', but '{db_row[SI.AVR_FILENAME]}' in database")


vprint(f"Processing file '{args.csv_file}'")
if allowed_file(args.csv_file) is not True:
    eprint(f"ERROR: only the file extensions {ALLOWED_EXTENSIONS} for the csv_file")
    exit(1)

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
    with open(args.csv_file, 'r', newline='') as csvfile:
         antibodycsv = csv.DictReader(csvfile, delimiter=',')
         csv_row_number = 1
         for csv_row in antibodycsv:
             csv_row_number = csv_row_number + 1
             # if len(csv_row) != CSV_ROWS:
             #    eprint(f"ERROR: Row should contain {CSV_ROWS} records but contains {len(csv_row)}")
             query: str = base_antibody_query(csv_row)
             cursor.execute(query)
             db_rows = cursor.fetchall()
             if len(db_rows) == 0:
                 eprint(f"ERROR: In file row {csv_row_number}; no rows found in database")
             elif len(db_rows) > 1:
                 eprint(f"WARNING: In file row {csv_row_number}; multiple rows found in database")
                 vprint(db_rows)
             for db_row in db_rows:
                 check_csv_row_to_db_row(csv_row, db_row)
                 check_es_entry_to_db_row(es_conn, args.elasticsearch_index, db_row)
                 avr_filename = db_row[SI.AVR_FILENAME]
                 if avr_filename is not None:
                    check_pdf_file_upload(args.assets_url, db_row[SI.AVR_UUID], avr_filename)

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
