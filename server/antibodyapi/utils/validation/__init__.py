import csv
import io
import PyPDF2
import requests
import re
from flask import abort
from urllib.parse import quote
import logging
from .. import allowed_file, json_error
from typing import List


logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


# This test should be the first one because subsequent tests depend on these keys existing in the row dict...
def validate_row_keys(row_i: int, row: dict) -> None:
    """
    For a list and definitions of these fields please see:
    https://software.docs.hubmapconsortium.org/avr/csv-format-v2.html
    """
    csv_header = [
        'uniprot_accession_number', 'hgnc_id', 'target_name', 'isotype', 'host', 'clonality',
        'vendor', 'catalog_number', 'lot_number', 'recombinant', 'concentration_value', 'dilution',
        'conjugate', 'rrid', 'method', 'tissue_preservation', 'protocols_doi', 'manuscript_doi',
        'author_orcid', 'vendor_affiliation', 'organ', 'organ_uberon', 'antigen_retrieval', 'avr_pdf_filename',
        'omap_id', 'cycle_number', 'fluorescent_reporter'
    ]

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


def value_present_in_row(value_key: str, row: dict) -> bool:
    return len(row[value_key].strip()) != 0


def validate_row_data_required_fields(row_i: int, row: dict) -> None:
    """
    These are fields in the data that cannot be empty as described in
    https://software.docs.hubmapconsortium.org/avr/csv-format-v2.html
    """
    required_item_keys: list[str] = [
        'uniprot_accession_number', 'hgnc_id', 'target_name', 'isotype', 'host', 'clonality',
        'vendor', 'catalog_number', 'lot_number', 'recombinant',
        'rrid', 'method', 'tissue_preservation', 'protocols_doi','manuscript_doi', 'author_orcid',
        'organ', 'organ_uberon', 'avr_pdf_filename', 'cycle_number'
    ]
    logger.debug(f'validate_row_data_required_fields: row: {row}')
    for item_key in required_item_keys:
        if len(row[item_key].strip()) == 0:
            abort(json_error(f"CSV file row# {row_i}: value for '{item_key}' is required", 406))

    # 'concentration_value' or 'dilution' but not both (e.g, xor).
    concentration_value_present: bool = value_present_in_row('concentration_value', row)
    dilution_present: bool = value_present_in_row('dilution', row)
    if not (concentration_value_present ^ dilution_present):
        abort(json_error(f"CSV file row# {row_i}: 'concentration_value' or 'dilution' but not both, and one must be present", 406))

    # 'cycle_number' and 'fluorescent_reporter' are required fields if 'omap_id' is present.
    cycle_number_present: bool = value_present_in_row('cycle_number', row)
    fluorescent_reporter_present: bool = value_present_in_row('fluorescent_reporter', row)
    omap_id_present: bool = value_present_in_row('omap_id', row)
    if omap_id_present and not (cycle_number_present and fluorescent_reporter_present):
        abort(json_error(f"CSV file row# {row_i}: 'cycle_number' and 'fluorescent_reporter' are required fields if 'omap_id' is present", 406))


def validate_row_data(row_i: int, row: dict) -> None:
    validate_row_data_required_fields(row_i, row)

    for item in row.values():
        validate_row_data_item_not_leading_trailing_whitespace(row_i, item)
        validate_row_data_item_isprintable(row_i, item)
        validate_row_data_item_not_linebreaks(row_i, item)

    # Validate specific values in an item....

    valid_recombinat: list[str] = ['yes', 'no']
    if row['recombinant'].lower() not in valid_recombinat:
        abort(json_error(f"CSV file row# {row_i}: recombinant value '{row['recombinant']}' is not one of: {', '.join(valid_recombinat)}", 406))

    # https://en.wikipedia.org/wiki/Clone_(cell_biology)
    valid_clonality: list[str] = ['polyclonal', 'oligoclonal', 'monoclonal']
    if row['clonality'] not in valid_clonality:
        abort(json_error(f"CSV file row# {row_i}: clonality value '{row['clonality']}' is not one of: {', '.join(valid_clonality)}", 406))

    if row['concentration_value'] != '':
        try:
            float(row['concentration_value'])
        except ValueError:
            abort(json_error(
                f"CSV file row# {row_i}: concentration_value '{row['concentration_value']}' must be numeric",
                406))

    dilution_re: re.Pattern = re.compile('^[0-9]+:[0-9]+$')
    if row['dilution'] != '' and dilution_re.match(row['dilution']) is None:
        abort(json_error(f"CSV file row# {row_i}: dilution '{row['dilution']}' must be of the form <integer>:<integer> (e.g. 1:100, 1:50, 1:2000)", 406))

    omap_id_re: re.Pattern = re.compile('^OMAP-[1-9][0-9]*$')
    if row['omap_id'] != '' and omap_id_re.match(row['omap_id']) is None:
        abort(json_error(f"CSV file row# {row_i}: omap_id '{row['omap_id']}' must be of the form OMAP-<integer> (e.g. OMAP-1, OMAP-2, ..., OMAP-n) ", 406))


def validate_protein_name(row_i: int, protein_name: str, primary_accession: str) -> None:
    """
    https://www.uniprot.org/help/api_queries
    """
    try:
        protein_name_url_encoded: str = protein_name.replace(' ', '%20')
        uniprot_rest_url: str = f"https://rest.uniprot.org/uniprotkb/search?query=protein_name:{protein_name_url_encoded}"
        logger.debug(f'validate_protein_name() URL: {uniprot_rest_url}')
        response = requests.get(uniprot_rest_url, headers={"Accept": "application/json"}, verify=False)
        if response.status_code == 200:
            response_json: dict = response.json()
            response_results: List[dict] = response_json.get('results')
            entry_list: List[dict] = [e for e in response_results if e.get('primaryAccession') == primary_accession]
            if len(entry_list) == 1:
                primary_accession_entry: dict = entry_list[0]
                logger.debug(f'validate_protein_name() entry: {primary_accession_entry}')
                if 'proteinDescription' in primary_accession_entry and \
                    'recommendedName' in primary_accession_entry['proteinDescription'] and \
                    'fullName' in primary_accession_entry['proteinDescription']['recommendedName'] and \
                    'value' in primary_accession_entry['proteinDescription']['recommendedName']['fullName'] and \
                    primary_accession_entry['proteinDescription']['recommendedName']['fullName']['value'] == protein_name:
                    return
        abort(json_error(f"CSV file row# {row_i}: Protein Name '{protein_name}' is not found in catalogue associated with uniprot_accession_number '{primary_accession}'", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating Protein Name '{protein_name}'", 406))
    finally:
        if response is not None:
            response.close()


def validate_uniprot_accession_number(row_i: int, uniprot_accession_number: str) -> None:
    try:
        uniprot_url: str = f"https://www.uniprot.org/uniprot/{uniprot_accession_number}.rdf?include=yes "
        logger.debug(f'validate_uniprot_accession_number() URL: {uniprot_url}')
        response = requests.get(uniprot_url, headers={"Accept": "application/json"}, verify=False)
        # https://www.uniprot.org/help/api_retrieve_entries
        if response.status_code == 404:
            abort(json_error(f"CSV file row# {row_i}: Uniprot Accession Number '{uniprot_accession_number}' is not found in catalogue",
                             406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating Uniprot Accession Number", 406))
    finally:
        if response is not None:
            response.close()


def validate_orcid(row_i: int, orcid: str) -> None:
    try:
        orcid_url: str = f"https://pub.orcid.org/{orcid}"
        logger.debug(f'validate_orcid() URL: {orcid_url}')
        response = requests.get(orcid_url, headers={"Accept": "application/json"}, verify=False)
        # TODO: 302
        if response.status_code == 404:
            abort(json_error(f"CSV file row# {row_i}: ORCID '{orcid}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered fetching ORCID", 406))
    finally:
        if response is not None:
            response.close()


def validate_rrid(row_i: int, rrid: str) -> None:
    try:
        rrid_url: str = f"https://scicrunch.org/resolver/RRID:{rrid}.json"
        logger.debug(f'validate_rrid() URL: {rrid_url}')
        response = requests.get(rrid_url, headers={"Accept": "application/json"}, verify=False)
        if response.status_code != 200:
            abort(json_error(f"CSV file row# {row_i}: RRID '{rrid}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating RRID '{rrid}'", 406))
    finally:
        if response is not None:
            response.close()


def validate_doi(row_i: int, doi: str) -> None:
    """
    https://www.doi.org/factsheets/DOIProxy.html
    2. Encoding DOIs for use in URIs
    Characters in DOI names that may not be interpreted correctly by web browsers, for example '?', should be encoded

    5. Proxy Server REST API
    Returns a JSON object with a "responseCode". Values are:
    1 : Success. (HTTP 200 OK)
    2 : Error. Something unexpected went wrong during handle resolution. (HTTP 500 Internal Server Error)
    100 : Handle Not Found. (HTTP 404 Not Found)
    200 : Values Not Found. The handle exists but has no values (or no values according to the types and indices specified). (HTTP 200 OK)
    """
    try:
        doi_url_base: str = "https://doi.org/api/handles/"
        doi_url: str = f"{doi_url_base}{quote(doi)}?type=URL"
        logger.debug(f'validate_doi() URL: {doi_url}')
        response = requests.get(doi_url, headers={"Accept": "application/json"}, verify=False)
        response_json: dict = response.json()
        if response.status_code != 200 or 'responseCode' not in response_json or response_json['responseCode'] != 1:
            abort(json_error(f"CSV file row# {row_i}: DOI '{doi}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating DOI '{doi}'", 406))
    finally:
        if response is not None:
            response.close()


def validate_hgnc(row_i: int, hgnc: str) -> None:
    """
    https://www.genenames.org/help/rest/
    Please only send REST requests at a rate of 10 requests per second
    If you experience 403 errors please contact us via our feedback form.

    Valid if 'response.numFound > 0'
    """
    try:
        hgnc_url_base: str = "https://rest.genenames.org/fetch/hgnc_id/"
        hgnc_url: str = f"{hgnc_url_base}{hgnc}"
        logger.debug(f'validate_hgnc() URL: {hgnc_url}')
        response = requests.get(hgnc_url, headers={"Accept": "application/json"}, verify=False)
        response_json: dict = response.json()
        if 'response' not in response_json or 'numFound' not in response_json['response']:
            abort(json_error(f"CSV file row# {row_i}: Problem encountered validating HGNC '{hgnc}'", 406))
        num_found: int = response_json['response']['numFound']
        if response.status_code != 200 or num_found <= 0:
            abort(json_error(f"CSV file row# {row_i}: HGNC '{hgnc}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating HGNC '{hgnc}'", 406))
    finally:
        if response is not None:
            response.close()


def validate_ontology(row_i: int, ontology_id: str, name: str) -> None:
    """
    https://www.ebi.ac.uk/ols/docs/api
    Ontology Search API

    ontology_id is a string of the form 'UBERON:0002113'.

    Valid if 'page.totalElements > 0'
    """
    try:
        ols_url_base: str = "http://www.ebi.ac.uk/ols/api/terms"
        ols_url: str = f"{ols_url_base}?id={ontology_id}"
        logger.debug(f'validate_ontology() URL: {ols_url}')
        response = requests.get(ols_url, headers={"Accept": "application/json"}, verify=False, allow_redirects=True)
        response_json: dict = response.json()
        if 'page' not in response_json or 'totalElements' not in response_json['page']:
            abort(json_error(f"CSV file row# {row_i}: Problem encountered validating Ontology ID '{ontology_id}'", 406))
        total_elements: int = response_json['page']['totalElements']
        if response.status_code != 200 or total_elements <= 0:
            abort(json_error(f"CSV file row# {row_i}: Ontology ID '{ontology_id}' is not found", 406))
        if '_embedded' in response_json and 'terms' in response_json['_embedded']:
            terms: List[dict] = response_json['_embedded']['terms']
            for term in terms:
                if 'annotation' in term and \
                    'has_related_synonym' in term['annotation'] and \
                    name in term['annotation']['has_related_synonym']:
                    return
        abort(json_error(f"CSV file row# {row_i}: Ontology ID '{ontology_id}'; related_synonym for '{name}' not found", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"CSV file row# {row_i}: Problem encountered validating RRID '{rrid}'", 406))
    finally:
        if response is not None:
            response.close()


def validate_antibodycsv_row(row_i: int, row: dict, request_files: dict) -> str:
    logger.debug(f"validate_antibodycsv_row: row# {row_i}: {row}")

    validate_row_keys(row_i, row)
    validate_row_data(row_i, row)

    found_pdf: str = None
    if 'pdf' in request_files:
        for avr_pdf_file in request_files.getlist('pdf'):
            if avr_pdf_file.filename == row['avr_pdf_filename']:
                content: bytes = avr_pdf_file.stream.read()
                # Since this is a stream, we need to go back to the beginning or the next time that it is read
                # it will be read from the end where there are no characters providing an empty file.
                avr_pdf_file.stream.seek(0)
                logger.debug(f"validate_antibodycsv_row: avr_pdf_file.filename: {row['avr_pdf_filename']}; size: {len(content)}")
                try:
                    PyPDF2.PdfFileReader(stream=io.BytesIO(content))
                    logger.debug(f"validate_antibodycsv_row: Processing avr_pdf_filename: {avr_pdf_file.filename}; is a valid PDF file")
                    found_pdf = avr_pdf_file.filename
                    break
                except PyPDF2.utils.PdfReadError:
                    abort(json_error(f"CSV file row# {row_i}: avr_pdf_filename '{row['avr_pdf_filename']}' found, but not a valid PDF file", 406))
        if found_pdf is None:
            abort(json_error(f"CSV file row# {row_i}: avr_pdf_filename '{row['avr_pdf_filename']}' is not found", 406))
    else:
        abort(json_error(f"CSV file row# {row_i}: avr_pdf_filename '{row['avr_pdf_filename']}' is not found", 406))

    # All of these make callouts to other RestAPIs...
    validate_uniprot_accession_number(row_i, row['uniprot_accession_number'])
    validate_hgnc(row_i, row['hgnc_id'])
    validate_protein_name(row_i, row['target_name'], row['uniprot_accession_number'])
    validate_rrid(row_i, row['rrid'])
    validate_doi(row_i, row['protocols_doi'])
    validate_orcid(row_i, row['author_orcid'])
    validate_ontology(row_i, row['organ_uberon'], row['organ'])
    validate_doi(row_i, row['manuscript_doi'])

    return found_pdf


def validate_antibodycsv(request_files: dict) -> list:
    """
    Currently called from import_antibodies (endpoint implementation of '/antibodies/import'.
    """
    pdf_files_processed: list = []
    for file in request_files.getlist('file'):
        if not file or file.filename == '':
            abort(json_error('Filename missing in uploaded files', 406))
        if file and allowed_file(file.filename):
            # TODO: remove any non-utf-8 characters from the stream both here and when processing it.
            lines: [str] = [x.decode("utf-8") for x in file.stream.read().splitlines()]
            logger.debug(f'Lines: {lines}')
            # Since this is a stream, we need to go back to the beginning or the next time that it is read
            # it will be read from the end where there are no characters providing an empty file.
            file.stream.seek(0)
            logger.debug(f"validate_antibodycsv: processing filename '{file.filename}' with {len(lines)} lines")
            row_i = 1
            for row_dr in csv.DictReader(lines, delimiter=','):
                row = {k.lower(): v for k, v in row_dr.items()}
                row_i = row_i + 1
                found_pdf: str = validate_antibodycsv_row(row_i, row, request_files)
                if found_pdf is not None:
                    logger.debug(f"validate_antibodycsv: CSV file row# {row_i}: found PDF file '{found_pdf}' as valid PDF")
                    pdf_files_processed.append(found_pdf)
                else:
                    logger.debug(f"validate_antibodycsv: CSV file row# {row_i}: valid PDF not found")
    logger.debug(f"validate_antibodycsv: found valid PDF files '{pdf_files_processed}'")
    return pdf_files_processed
