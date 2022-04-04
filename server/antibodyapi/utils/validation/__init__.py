import csv
import re
import io
import PyPDF2
import requests
from flask import abort
import logging
from .. import allowed_file, json_error
from typing import List


logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


# This test should be the first one because subsequent tests depend on these keys existing in the row dict...
def validate_row_keys(row_i: int, row: dict) -> None:
    csv_header = [
        'protocols_io_doi', 'uniprot_accession_number', 'target_name', 'rrid', 'antibody_name',
        'host_organism', 'clonality', 'vendor', 'catalog_number', 'lot_number', 'recombinant',
        'organ_or_tissue', 'hubmap_platform', 'submitter_orcid', 'avr_filename']

    if len(row) != len(csv_header):
        abort(json_error(f"CSV file row# {row_i}: Has {len(row)} elements but should have {len(csv_header)}", 406))
    for key in csv_header:
        if key not in row:
            abort(json_error(f"CSV file row# {row_i}: Key '{key}' is not present", 406))


def validate_row_data_item_not_leading_trailing_whitespace(row_i: int, item: str) -> None:
    if len(item) > 0 and (item[0].isspace() or item[-1].isspace()):
        abort(json_error(
            f"CSV file row# {row_i}: a leading or trailing whitespace characters are not permitted in a data item",
            406))


def validate_row_data_item_isprintable(row_i: int, item: str) -> None:
    if not item.isprintable():
        abort(json_error(
            f"CSV file row# {row_i}: non-printable characters are not permitted in a data item",
            406))


# This may not be necessary, but there is some confusion in blog posts as to what isprintable() considers printable
def validate_row_data_item_not_linebreaks(row_i: int, item: str) -> None:
    lines: List[str] = item.splitlines()
    if len(lines) > 1:
        abort(json_error(
            f"CSV file row# {row_i}: line break characters are not permitted in a data item",
            406))


def validate_row_data(row_i: int, row: dict) -> None:
    for item in row.values():
        validate_row_data_item_not_leading_trailing_whitespace(row_i, item)
        validate_row_data_item_isprintable(row_i, item)
        validate_row_data_item_not_linebreaks(row_i, item)

    valid_recombinat: list[str] = ['true', 'false']
    if row['recombinant'] not in valid_recombinat:
        abort(json_error(f"CSV file row# {row_i}: recombinant value '{row['recombinant']}' is not one of: {', '.join(valid_recombinat)}", 406))

    # https://en.wikipedia.org/wiki/Clone_(cell_biology)
    valid_clonality: list[str] = ['polyclonal', 'oligoclonal', 'monoclonal']
    if row['clonality'] not in valid_clonality:
        abort(json_error(f"CSV file row# {row_i}: clonality value '{row['clonality']}' is not one of: {', '.join(valid_clonality)}", 406))


def validate_uniprot_accession_number(row_i: int, uniprot_accession_number: str) -> None:
    try:
        uniprot_url: str = f"https://www.uniprot.org/uniprot/{uniprot_accession_number}.rdf?include=yes "
        response = requests.get(uniprot_url)
        # https://www.uniprot.org/help/api_retrieve_entries
        if response.status_code == 404:
            abort(json_error(f"CSV file row# {row_i}: Uniprot Accession Number '{uniprot_accession_number}' is not found in catalogue",
                             406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating Uniprot Accession Number", 406))


def validate_submitter_orcid(row_i: int, submitter_orcid: str) -> None:
    try:
        orcid_url: str = f"https://pub.orcid.org/{submitter_orcid}"
        response = requests.get(orcid_url)
        # TODO: 302
        if response.status_code == 404:
            abort(json_error(f"CSV file row# {row_i}: ORCID '{submitter_orcid}' is not found in catalogue",
                             406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered fetching ORCID", 406))


def validate_rrid(row_id: int, rrid: str) -> None:
    # TODO: The rrid search is really fragile and a better way should be found
    try:
        rrid_url: str = f"https://antibodyregistry.org/search?q={rrid}"
        response = requests.get(rrid_url)
        if re.search(r'0 results out of 0 with the query', response.text):
            abort(json_error(f"CSV file row# {row_i}: RRID '{rrid}' is not valid", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating RRID", 406))


def validate_antibodycsv_row(row_i: int, row: dict, request_files: dict) -> str:
    logger.debug(f"validate_antibodycsv_row: row {row_i}: {row}")

    validate_row_keys(row_i, row)
    validate_row_data(row_i, row)

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

    validate_uniprot_accession_number(row_i, row['uniprot_accession_number'])
    validate_submitter_orcid(row_i, row['submitter_orcid'])
    validate_rrid(row_i, row['rrid'])

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
