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

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
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

    # Validate everything before saving anything...
    pdf_files_processed: list = validate_antibodycsv(request.files)

    for file in request.files.getlist('file'):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            logger.info(f"import_antibodies: processing filename: {filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename)) as csvfile:
                antibodycsv = csv.DictReader(csvfile, delimiter=',')
                row_i = 1
                for row in antibodycsv:
                    row_i = row_i + 1
                    try:
                        row['vendor_id'] = find_or_create_vendor(cur, row['vendor'])
                    except KeyError:
                        abort(json_error(f"CSV file row# {row_i}: Problem processing Vendor field", 406))
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
                        abort(json_error(f"CSV file row# {row_i}: Antibody not unique", 406))
        else:
            abort(json_error('Filetype forbidden', 406))

    pdf_files_not_processed: list = []
    for avr_file in request.files.getlist('pdf'):
        if avr_file.filename not in pdf_files_processed:
            pdf_files_not_processed.append(avr_file.filename)
    return make_response(jsonify(antibodies=uuids_and_names, pdf_files_not_processed=pdf_files_not_processed), 201)


csv_header = [
    'protocols_io_doi', 'uniprot_accession_number', 'target_name', 'rrid', 'antibody_name',
    'host_organism', 'clonality', 'vendor', 'catalog_number', 'lot_number', 'recombinant',
    'organ_or_tissue', 'hubmap_platform', 'submitter_orciid', 'avr_filename']


def validate_antibodycsv_row(row_i: int, row: dict, request_files: dict) -> str:
    logger.debug(f"validate_antibodycsv_row: row {row_i}: {row}")

    if len(row) != len(csv_header):
        abort(json_error(f"CSV file row# {row_i}: Has {len(row)} elements but should have {len(csv_header)}", 406))
    for key in csv_header:
        if key not in row:
            abort(json_error(f"CSV file row# {row_i}: Key '{key}' is not present", 406))

    for item in row:
        if '\n' in item:
            abort(json_error(f"CSV file row# {row_i}: the new line character is not permitted in a data item", 406))

    valid_recombinat: list[str] = ['true', 'false']
    if row['recombinant'] not in valid_recombinat:
        abort(json_error(f"CSV file row# {row_i}: recombinant value '{row['recombinant']}' is not one of: {', '.join(valid_recombinat)}", 406))

    # https://en.wikipedia.org/wiki/Clone_(cell_biology)
    valid_clonality: list[str] = ['polyclonal', 'oligoclonal', 'monoclonal']
    if row['clonality'] not in valid_clonality:
        abort(json_error(f"CSV file row# {row_i}: clonality value '{row['clonality']}' is not one of: {', '.join(valid_clonality)}", 406))

    found_pdf: str = None
    if 'pdf' in request_files:
        for avr_file in request_files.getlist('pdf'):
            if avr_file.filename == row['avr_filename']:
                content: bytes = avr_file.stream.read()
                # Since this is a stream, we need to go back to the beginning or the next time that it is read
                # it will be read from the end where there are no characters providing an empty file.
                avr_file.stream.seek(0)
                logger.debug(f"validate_antibodycsv_row: avr_file.filename: {row['avr_filename']}; size: {len(content)}")
                try:
                    PyPDF2.PdfFileReader(stream=io.BytesIO(content))
                    logger.debug(f"validate_antibodycsv_row: Processing avr_filename: {avr_file.filename}; is a valid PDF file")
                    found_pdf = avr_file.filename
                    break
                except PyPDF2.utils.PdfReadError:
                    abort(json_error(f"CSV file row# {row_i}: avr_filename '{row['avr_filename']}' found, but not a valid PDF file", 406))
        if found_pdf is None:
            abort(json_error(f"CSV file row# {row_i}: avr_filename '{row['avr_filename']}' is not found", 406))
    else:
        abort(json_error(f"CSV file row# {row_i}: avr_filename '{row['avr_filename']}' is not found", 406))

    try:
        uniprot_url: str = f"https://www.uniprot.org/uniprot/{row['uniprot_accession_number']}.rdf?include=yes "
        response = requests.get(uniprot_url)
        # https://www.uniprot.org/help/api_retrieve_entries
        if response.status_code == 404:
            abort(json_error(f"CSV file row# {row_i}: Uniprot Accession Number '{row['uniprot_accession_number']}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating Uniprot Accession Number", 406))

    try:
        orcid_url: str = f"https://pub.orcid.org/{row['submitter_orciid']}"
        response = requests.get(orcid_url)
        if response.status_code == 404:
            abort(json_error(f"CSV file row# {row_i}: ORCID '{row['submitter_orciid']}' is not found in catalogue",
                             406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered fetching ORCID", 406))

    # TODO: The rrid search is really fragile and a better way should be found
    try:
        rrid_url: str = f"https://antibodyregistry.org/search?q={row['rrid']}"
        response = requests.get(rrid_url)
        if re.search(r'0 results out of 0 with the query', response.text):
            abort(json_error(f"CSV file row# {row_i}: RRID '{row['rrid']}' is not valid", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating RRID", 406))
    # TODO: Make sure that the .pdf file was uploaded and that it really was a .pdf file.

    return found_pdf


def validate_antibodycsv(request_files: dict) -> list:
    pdf_files_processed: list = []
    for file in request_files.getlist('file'):
        if not file or file.filename == '':
            abort(json_error('Filename missing in uploaded files', 406))
        if file and allowed_file(file.filename):
            lines: [str] = [x.decode("utf-8") for x in file.stream.readlines()]
            # Since this is a stream, we need to go back to the beginning or the next time that it is read
            # it will be read from the end where there are no characters providing an empty file.
            file.stream.seek(0)
            logger.debug(f"validate_antibodycsv: processing filename '{file.filename}' with {len(lines)} lines")
            row_i = 1
            for row in csv.DictReader(lines, delimiter=','):
                row_i = row_i + 1
                found_pdf: str = validate_antibodycsv_row(row_i, row, request_files)
                if found_pdf is not None:
                    logger.debug(f"validate_antibodycsv: CSV file row# {row_i}: found PDF file '{found_pdf}' as valid PDF")
                    pdf_files_processed.append(found_pdf)
                else:
                    logger.debug(f"validate_antibodycsv: CSV file row# {row_i}: valid PDF not found")
    logger.debug(f"validate_antibodycsv: found valid PDF files '{pdf_files_processed}'")
    return pdf_files_processed
