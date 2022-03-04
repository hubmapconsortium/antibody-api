import csv
import os
from flask import (
    abort, Blueprint, current_app, jsonify, make_response,
    redirect, request, session, url_for
)
from psycopg2.errors import UniqueViolation #pylint: disable=no-name-in-module
from werkzeug.utils import secure_filename
from antibodyapi.utils import (
    allowed_file, find_or_create_vendor, get_cursor,
    get_file_uuid, get_group_id, get_hubmap_uuid,
    insert_query, insert_query_with_avr_file_and_uuid,
    json_error
)
from antibodyapi.utils.elasticsearch import index_antibody
import requests
import re
import PyPDF2
import io
import logging
import pprint

import_antibodies_blueprint = Blueprint('import_antibodies', __name__)

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


@import_antibodies_blueprint.route('/antibodies/import', methods=['POST'])
def import_antibodies(): # pylint: disable=too-many-branches
    authenticated = session.get('is_authenticated')
    if not authenticated:
        return redirect(url_for('login'))

    if 'file' not in request.files:
        abort(json_error('CSV file missing', 406))

    app = current_app
    cur = get_cursor(app)
    uuids_and_names = []

    group_id = get_group_id(
        app.config['INGEST_API_URL'], request.form.get('group_id')
    )

    if group_id is None:
        abort(json_error('Not a member of a data provider group or no group_id provided', 406))

    for file in request.files.getlist('file'):
        if file.filename == '':
            abort(json_error('Filename missing', 406))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename)) as csvfile:
                antibodycsv = csv.DictReader(csvfile, delimiter=',')
                row_i = 1
                for row in antibodycsv:
                    row_i = row_i + 1
                    validate_antibodycsv_row(row_i, row, request.files)
                    try:
                        row['vendor_id'] = find_or_create_vendor(cur, row['vendor'])
                    except KeyError:
                        abort(json_error('CSV fields are wrong', 406))
                    vendor = row['vendor']
                    del row['vendor']
                    row['antibody_uuid'] = get_hubmap_uuid(app.config['UUID_API_URL'])
                    row['created_by_user_displayname'] = session['name']
                    row['created_by_user_email'] = session['email']
                    row['created_by_user_sub'] = session['sub']
                    row['group_uuid'] = group_id
                    query = insert_query()
                    if 'avr_filename' in row.keys():
                        if 'pdf' in request.files:
                            for avr_file in request.files.getlist('pdf'):
                                if avr_file.filename == row['avr_filename']:
                                    row['avr_uuid'] = get_file_uuid(
                                        app.config['INGEST_API_URL'],
                                        app.config['UPLOAD_FOLDER'],
                                        row['antibody_uuid'],
                                        avr_file
                                    )
                                    query = insert_query_with_avr_file_and_uuid()
                    try:
                        cur.execute(query, row)
                        uuids_and_names.append({
                            'antibody_name': row['antibody_name'],
                            'antibody_uuid': row['antibody_uuid']
                        })
                        index_antibody(row | {'vendor': vendor})
                    except KeyError:
                        abort(json_error('CSV fields are wrong', 406))
                    except UniqueViolation:
                        abort(json_error('Antibody not unique', 406))
        else:
            abort(json_error('Filetype forbidden', 406))
    return make_response(jsonify(antibodies=uuids_and_names), 201)


csv_header = [
    'protocols_io_doi', 'uniprot_accession_number', 'target_name', 'rrid', 'antibody_name',
    'host_organism', 'clonality', 'vendor', 'catalog_number', 'lot_number', 'recombinant',
    'organ_or_tissue', 'hubmap_platform', 'submitter_orciid', 'avr_filename']


def validate_antibodycsv_row(row_i: int, row: dict, request_files: dict) -> None:
    if len(row) != len(csv_header):
        abort(json_error(f"CSV file row# {row_i}: Has {len(row)} elements but should have {len(csv_header)}", 406))
    for key in csv_header:
        if key not in row:
            abort(json_error(f"CSV file row# {row_i}: Key '{key}' is not present", 406))

    try:
        uniprot_url: str = f"https://www.uniprot.org/uniprot/{row['uniprot_accession_number']}.rdf?include=yes "
        response = requests.get(uniprot_url)
        # https://www.uniprot.org/help/api_retrieve_entries
        if response.status_code == 404:
            abort(json_error(f"CSV file row# {row_i}: Uniprot Accession Number '{row['uniprot_accession_number']}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        abort(json_error(f"CSV file row# {row_i}: Problem encountered fetching Uniprot Accession Number", 406))

    try:
        orcid_url: str = f"https://pub.orcid.org/{row['submitter_orciid']}"
        response = requests.get(orcid_url)
        if response.status_code == 404:
            abort(json_error(f"CSV file row# {row_i}: ORCID '{row['submitter_orciid']}' is not found in catalogue",
                             406))
    except requests.ConnectionError as error:
        abort(json_error(f"CSV file row# {row_i}: Problem encountered fetching ORCID", 406))

    # TODO: The rrid search is really fragile and a better way should be found
    try:
        rrid_url: str = f"https://antibodyregistry.org/search?q={row['rrid']}"
        response = requests.get(rrid_url)
        if re.search(r'0 results out of 0 with the query', response.text):
            abort(json_error(f"CSV file row# {row_i}: RRID '{row['rrid']}' is not valid", 406))
    except requests.ConnectionError as error:
        abort(json_error(f"CSV file row# {row_i}: RRID '{row['rrid']}' is not valid", 406))
    # TODO: Make sure that the .pdf file was uploaded and that it really was a .pdf file.

    if row['recombinant'] not in ['true', 'false']:
        abort(json_error(f"CSV file row# {row_i}: recombinant '{row['recombinant']}' is not 'true' of 'false'", 406))

    if 'pdf' in request_files:
        found: bool = False
        for avr_file in request_files.getlist('pdf'):
            if avr_file.filename == row['avr_filename']:
                found = True
                content: bytes = avr_file.read()
                try:
                    PyPDF2.PdfFileReader(stream=io.BytesIO(content))
                    logger.debug(f"Processing avr_filename: {avr_file.filename}; is a valid .pdf file")
                except PyPDF2.utils.PdfReadError:
                    abort(json_error(f"CSV file row# {row_i}: avr_filename '{row['avr_filename']}' found, but not a valid .pdf file", 406))
        if not found:
            abort(json_error(f"CSV file row# {row_i}: avr_filename '{row['avr_filename']}' is not found", 406))
    else:
        abort(json_error(f"CSV file row# {row_i}: avr_filename '{row['avr_filename']}' is not found", 406))