import logging
import string
import argparse
import time
import datetime
import requests
import psycopg2
from psycopg2._psycopg import connection
# import sys
# sys.path.insert(0, "../../server/antibodyapi/utils/validate_items")
# from validation_exception import ValidationError
# from validation_utils import CanonicalizeYNResponse, CanonicalizeDOI

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    filename='./updates_from_csv.log',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def parse_cfg(cfg_file: str) -> dict:
    """
    Parse a .cfg file to a dict.
    """
    conf: dict = {}
    with open(cfg_file) as fp:
        for line in fp:
            line: str = line.strip()
            if line.startswith('#') or len(line) == 0:
                continue
            line = line.rstrip('\n')
            key, val = line.strip().split('=', 1)
            key: str = key.strip()
            conf[key] = val.strip().strip("'\"")
    return conf


VALID_COLUMNS: list = [
    'antibody_uuid', 'protocol_doi', 'uniprot_accession_number', 'target_symbol', 'rrid', 'host', 'cell_line',
    'cell_line_ontology_id', 'clonality', 'clone_id', 'vendor_id', 'catalog_number', 'lot_number', 'recombinant',
    'organ', 'method', 'author_orcids', 'hgnc_id', 'isotype', 'concentration_value', 'dilution_factor', 'conjugate',
    'tissue_preservation', 'cycle_number', 'fluorescent_reporter', 'manuscript_doi', 'vendor_affiliation',
    'organ_uberon_id', 'antigen_retrieval', 'omap_id', 'created_timestamp', 'created_by_user_displayname',
    'created_by_user_email', 'created_by_user_sub', 'group_uuid', 'antibody_hubmap_id'
]
VENDORS_TABLE: str = 'public.vendors'
ANTIBODIES_TABLE: str = 'public.antibodies'


def only_printable_and_strip(s: str) -> str:
    """
    Return a string that contains only printable characters found in 's'.
    """
    # We use the more restrictive string.printable which does not contain unicode characters.
    return ''.join(c for c in s if c in string.printable).strip()


def make_db_connection(user: str, password: str, host: str, dbname: str) -> connection:
    logger.info(f"make_db_connection host:{host}, user:{user}, dbname:{dbname}")
    try:
        db_conn: connection = psycopg2.connect(user=user, password=password, host=host, dbname=dbname)
    except psycopg2.Error as e:
        logger.error(f"Unable to connect to PosgreSQL database: {dbname} on host: {host}; error: {e}")
        exit(1)
    if db_conn.closed == 0:
        logger.info(f"make_db_connection successfully connected")
    else:
        logger.error(f"make_db_connection is CLOSED?!")
        exit(1)
    return db_conn


def find_or_create_vendor(cursor, vendor_name) -> int:
    """
    Look for the vendor_name in the VENDOR_TABLE, if found return the vendor_id,
    if not found create an entry for it returning the vendor_id.
    """
    cursor.execute('SELECT id FROM vendors WHERE UPPER(vendor_name) = %s', (vendor_name.upper(),))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        cursor.execute('INSERT INTO vendors (vendor_name) VALUES (%s) RETURNING id', (vendor_name,))
        return cursor.fetchone()[0]


def confirm_existance_of_antibody_hubmap_id(conn, antibody_hubmap_id: str) -> bool:
    """
    Return True if the 'antibody_humbmap_id' exists exists in the database, False if it does not.
    """
    stmt: str = f"SELECT count(*) from {ANTIBODIES_TABLE} where antibody_hubmap_id = %s"
    cur = conn.cursor()
    cur.execute(stmt, (antibody_hubmap_id,))
    row_count = cur.fetchone()
    return row_count[0] != 0


def make_update(conn, csv_header: list, line_items: list) -> None:
    """
    Update the database record changing the values of the fields in 'csv_header' to that in 'line_items'.
    The record changed is that which has the 'antibody_hubmap_id'.
    """
    antibody_hubmap_id = None
    stmt: str = f'UPDATE {ANTIBODIES_TABLE} SET'
    for i in range(len(csv_header)):
        header_item = csv_header[i]
        line_item = line_items[i]
        if csv_header[i] == 'antibody_hubmap_id':
            antibody_hubmap_id = line_item
            if confirm_existance_of_antibody_hubmap_id(conn, antibody_hubmap_id) is False:
                logger.error(f"The antibody_hubmap_id specified '{antibody_hubmap_id}' does not exist in the table {ANTIBODIES_TABLE}?")
                exit(1)
        else:
            if header_item == 'vendor_affiliation':
                try:
                    cur = conn.cursor()
                    line_item = find_or_create_vendor(cur, line_item)
                    cur.close()
                except psycopg2.Error as pe:
                    logger.error(f"Fatal error while executing get_id_for_vendor: {pe}")
                    exit(1)
                header_item = 'vendor_id'
            stmt += f" {header_item} = '{line_item}'"
            if i < len(csv_header)-2:
                stmt += ","
    stmt += f" WHERE antibody_hubmap_id = '{antibody_hubmap_id}';"
    try:
        cur = conn.cursor()
        cur.execute(stmt)
        conn.commit()
        cur.close()
    except psycopg2.Error as pe:
        logger.error(f"Fatal error while executing make_update; stmt: {stmt}: {pe}")
        exit(1)
    logger.info(f"Update successful forantibody_hubmap_id: {antibody_hubmap_id}")


class RawTextArgumentDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter
):
    pass


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        print('error: %s\n' % message)
        self.print_help()
        exit(2)


parser = MyParser(
    description='''
    This is a script to change entries in the database using the 'csv_file' provided, and then restore ElasticSearch.
    
    For the 'token' parameter, login through the UI to get the credentials for the environment that you are using.
    https://ingest.dev.hubmapconsortium.org/ (DEV)
    https://ingest.test.hubmapconsortium.org/ (TEST)
    https://ingest.hubmapconsortium.org/ (PROD)
    In Firefox (Tools > Browser Tools > Web Developer Tools).
    Click on "Storage" then the dropdown for "Local Storage" and then the url,
    Take the 'groups_token' as the 'token' parameter.
    
    Example of usage:
    python3 -m venv venv
    source venv/bin/activate
    pip3 install --upgrade pip
    pip3 install -r ./requirements.txt
    python3 ./update_from_csv.py ./app.conf ./dev_test.csv token
    ''',
    formatter_class=RawTextArgumentDefaultsHelpFormatter)
parser.add_argument('cfg_file',
                    help='Configuration file (instance/app.cfg).')
parser.add_argument('csv_file',
                    help='CSV file containing a header (columns) and data lines of changes to be made.'
                         'It must contain a antibody_hubmap_id')
parser.add_argument('token',
                    help='Bearer token used in calling endpoint AVR/restore_elasticsearch')

start_time = time.time()

args = parser.parse_args()

config = parse_cfg(args.cfg_file)

conn = make_db_connection(config['DATABASE_USER'], config['DATABASE_PASSWORD'],
                          config['DATABASE_HOST'], config['DATABASE_NAME'])

csv_file_stream = open(args.csv_file, 'r')
csv_file_lines = csv_file_stream.readlines()

# Do some checks on the .csv file header and data....
csv_file_header: list = [only_printable_and_strip(c) for c in csv_file_lines[0].split(',')]
csv_file_header_len: int = len(csv_file_header)
for column in csv_file_header:
    if column not in VALID_COLUMNS:
        logger.error(f'csv_file header contains an invalid column name: {column}')
        logger.error(f"valid columns are: {', '.join(VALID_COLUMNS)}")
        exit(1)
if 'antibody_hubmap_id' not in csv_file_header:
    logger.error('csv_file header must contain the column: antibody_hubmap_id')
    exit(1)
line_no = 1
for line in csv_file_lines[1:]:
    line_items: list = [only_printable_and_strip(c) for c in line.split(',')]
    if csv_file_header_len != len(line_items):
        logger.error(f"csv_file data line# {line_no} must have the same number of items as the header line")
        exit(1)
    line_no += 1
logger.info(f"Checks on scv file '{args.csv_file}' passed.")

for line in csv_file_lines[1:]:
    line_items: list = [only_printable_and_strip(c) for c in line.split(',')]
    try:
        make_update(conn, csv_file_header, line_items)
    except psycopg2.OperationalError as oe:
        logger.error(f"PosgreSql Operational Error: {oe}")
logger.info(f"Processed {len(csv_file_lines[1:])} records")

conn.close()

avr_api_url: str = config['AVR_API_URL'].rstrip('/')
restore_elasticsearch_url: str = f"{avr_api_url}/restore_elasticsearch"
headers: dict = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {args.token}"
}
response = requests.put(restore_elasticsearch_url, headers=headers)
if response.status_code != 200:
    logger.error(f"Restore ElasticSearch failed; status:{response.status_code}")
    exit(1)
logger.info(f"Restore ElasticSearch succeeded")

logger.info(f"Run Time: {datetime.timedelta(seconds=time.time() - start_time)}")
logger.info('Done!')
