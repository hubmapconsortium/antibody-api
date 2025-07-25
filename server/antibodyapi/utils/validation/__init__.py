import csv
import io
import psycopg2
from pypdf import PdfReader
from pypdf.errors import PdfReadError
import requests
import re
from flask import abort, make_response, jsonify, current_app
from urllib.parse import quote
import logging
from typing import List
import time
import datetime
from werkzeug.exceptions import HTTPException


logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'tsv'}


class CanonicalizeYNResponse:
    """
    Used to canonicalize or to convert the 'one of many' acceptable values of 'resp' into a single standard form.
    This allows for consistency when storing the 'resp' in a database.

    The standard form of 'resp' is returned, or None if there is no match.
    """
    affermative: List[str] = ['yes', 'y', 'true', 't']
    negative: List[str] = ['no', 'n', 'false', 'f']

    def canonicalize(self, resp: str):
        if resp.lower() in self.affermative:
            return self.affermative[0].capitalize()
        if resp.lower() in self.negative:
            return self.negative[0].capitalize()
        return None

    def valid(self):
        return [].extend(self.affermative).extend(self.negative)


class CanonicalizeDOI:
    """
    Used to canonicalize the DOI.

    We look for one of three prefixes and strip it returning the DOI or None if no prefixes are found.

    The official DOI handbook: doi:10.1000/182
    The SOP: AVR construction lists: https://doi.org/… or https://dx.doi.org/…
    """
    prefixes: List[str] = ['doi:', 'https://doi.org/', 'https://dx.doi.org/']

    def canonicalize(self, original_doi: str):
        for prefix in self.prefixes:
            doi = original_doi.removeprefix(prefix)
            if len(doi) < len(original_doi):
                return doi
        return None

    def canonicalize_multiple(self, original_dois: str) -> str:
        canonicalised_dois: str = ""
        for doi in original_dois.split(','):
            canonicalised_doi = self.canonicalize(doi.strip())
            if canonicalised_doi is not None:
                if canonicalised_dois != "":
                    canonicalised_dois += ","
                canonicalised_dois += canonicalised_doi
        return canonicalised_dois

    def valid(self):
        return self.prefixes


def json_error(message: str, error_code: int):
    logger.info(f'JSON_ERROR Response; message: {message}; error_code: {error_code}')
    return make_response(jsonify(message=message), error_code)


tsv_header_keys: List[str] = [
    'uniprot_accession_number', 'hgnc_id', 'target_symbol', 'isotype', 'host', 'clonality', 'clone_id', 
    'vendor', 'catalog_number', 'lot_number', 'recombinant', 'concentration_value',
    'dilution_factor', 'conjugate', 'rrid', 'method', 'tissue_preservation', 'protocol_doi', 'manuscript_doi',
    'author_orcids', 'vendor_affiliation', 'organ', 'organ_uberon_id', 'antigen_retrieval', 'avr_pdf_filename',
    'omap_id', 'cycle_number', 'fluorescent_reporter', 'previous_version_id'
]




def validate_row_data_item_isprintable(row_i: int, item: str) -> None:
    if not item.isprintable():
        abort(json_error(
            f"TSV file row# {row_i}: non-printable characters are not permitted in a data item",
            406))


# This may not be necessary, but there is some confusion in blog posts as to what isprintable() considers printable
def validate_row_data_item_not_linebreaks(row_i: int, item: str) -> None:
    lines: List[str] = item.splitlines()
    if len(lines) > 1:
        abort(json_error(
            f"TSV file row# {row_i}: line break characters are not permitted in a data item",
            406))


def value_present_in_row(value_key: str, row: dict) -> bool:
    return len(row[value_key].strip()) != 0


def validate_row_data_required_fields(row_i: int, row: dict) -> None:
    """
    This routine tests for adherence to a number of rules:

    0) items in the 'required_item_keys' must always be present (e.g., not the empty string).
    1) 'concentration_value' or 'dilution_factor' but not both (e.g, xor).
    2) 'clone_id' will be non-blank when 'clonality' contains 'monoclonal', if 'clonality' contains 'polyclonal' then 'clone_id' will/should be blank.
    3) if 'organ' is present then 'organ_uberon_id' must be present.
    """
    # Ellen Quardokus Aug 1, 2023
    # Remove: 'cycle_number' and 'isotype' as 'fields that should always be present' and make them both optional.

    logger.debug(f'validate_row_data_required_fields: row: {row}')

    # 'concentration_value' or 'dilution_factor' but not both (e.g, xor).
    concentration_value_present: bool = value_present_in_row('concentration_value', row)
    dilution_factor_present: bool = value_present_in_row('dilution_factor', row)
    if not (concentration_value_present ^ dilution_factor_present):
        abort(json_error(f"TSV file row# {row_i}: 'concentration_value' or 'dilution_factor'"
                         " but not both, and one must be present", 406))

    organ_present: bool = value_present_in_row('organ', row)

    # 'clone_id' will be non-blank when 'clonality' contains 'monoclonal',
    # if 'clonality' contains 'polyclonal' then 'clone_id' will/should be blank. Ellen in Slack on Jul 20, 2023
    clonality: str = row['clonality'].lower()
    clone_id: str = row['clone_id']
    if (clonality == 'monoclonal' and len(clone_id) == 0) or\
            (clonality != 'monoclonal' and len(clone_id) > 0):
        abort(json_error(f"TSV file row# {row_i}: When clonality is 'monoclonal' then 'clone_id'"
                         " must be specified otherwise 'clone_id' should not be specified", 406))

    # if 'organ' is present then 'organ_uberon_id' must be present.
    organ_uberon_id_present: bool = value_present_in_row('organ_uberon_id', row)
    if organ_present ^ organ_uberon_id_present:
        abort(json_error(f"TSV file row# {row_i}: Both 'organ' and 'organ_uberon_id'"
                         " must be present if any one of them are present", 406))

    # 'cycle_number' and 'fluorescent_reporter' are required fields if 'omap_id' is present.
    # cycle_number_present: bool = value_present_in_row('cycle_number', row)
    # fluorescent_reporter_present: bool = value_present_in_row('fluorescent_reporter', row)
    # omap_id_present: bool = value_present_in_row('omap_id', row)
    # if omap_id_present and not (cycle_number_present and fluorescent_reporter_present):
    #     abort(json_error(f"TSV file row# {row_i}: 'cycle_number' and 'fluorescent_reporter'"
    #                      " are required fields if 'omap_id' is present", 406))


def validate_row_data(row_i: int, row: dict) -> None:
    validate_row_data_required_fields(row_i, row)

    for item in row.values():
        validate_row_data_item_isprintable(row_i, item)
        validate_row_data_item_not_linebreaks(row_i, item)

    # Validate specific values in an item....

    # TODO: Later normalize this so that when it's stored in the DB it's either 'y' or 'n'
    canonicalize_yn_response = CanonicalizeYNResponse()
    if canonicalize_yn_response.canonicalize(row['recombinant']) is None:
        abort(json_error(f"TSV file row# {row_i}: recombinant value '{row['recombinant']}'"
                         f" is not one of: {', '.join(canonicalize_yn_response.valid())}", 406))


def validate_targets(row_i: int, targets: str, ubkg_api_url: str) -> dict:
    """
    Since the target_symbol can be a comma delimited string, the validated target_symbol must also be one.
    The aliases of each to the array of aliases must be combine so that they can all be searched on through
    ElasticSearch.
    """
    result: dict = {targets: {"target_symbol": "", "target_aliases": []}}
    for target in targets.split(','):
        target_strip = target.strip()
        validated = validate_target(row_i, target_strip, ubkg_api_url)
        validated_data = validated[target_strip]
        if result[targets]["target_symbol"] != "":
            result[targets]["target_symbol"] += ","
        result[targets]["target_symbol"] += validated_data["target_symbol"]
        result[targets]["target_aliases"] += validated_data["target_aliases"]
    # remove duplicates from the target_aliases
    result[targets]["target_aliases"] = list(set(result[targets]["target_aliases"]))
    return result


def validate_target(row_i: int, target: str, ubkg_api_url: str) -> dict:
    """
    Look up the target using the UBKG API endpoint.

    The UBKG endpoint will return a status of 200 if it finds the target with a dict for that
    target containing target entries that are: approved, alias, and previous.
    The approved is used rather than the target in the database as the target_symbol.
    The user can then search on any of the entries returned for the target in target_aliases.
    """
    response = None
    try:
        target_encoded: str = target.replace(' ', '%20')
        ubkg_rest_url: str = f"{ubkg_api_url}/relationships/gene/{target_encoded}"
        logger.debug(f'validate_target() URL: {ubkg_rest_url}')
        response = requests.get(ubkg_rest_url, headers={"Accept": "application/json"}, verify=False)
        if response.status_code == 200:
            response_json: dict = response.json()
            target_symbol: str = response_json["symbol-approved"][0]
            target_aliases: list = [target_symbol] + response_json["symbol-alias"] + response_json["symbol-previous"]
            return {target: {"target_symbol": target_symbol, "target_aliases": target_aliases}}
        elif response.status_code == 404:
            abort(json_error(f"TSV file row# {row_i}: target_symbol '{target}' is not found", 406))
        else:
            abort(json_error(f"TSV file row# {row_i}: Problem encountered validating target_symbol '{target}'", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"TSV file row# {row_i}: Problem encountered validating target_symbol '{target}'", 406))
    finally:
        if response is not None:
            response.close()

def validate_previous_version_id(row_i: int, previous_version_id: str, cur) -> None:
    if not previous_version_id.strip():
        return
    try:
        cur.execute("""
            SELECT next_version_id 
            FROM antibodies 
            WHERE antibody_hubmap_id = %s
        """, (previous_version_id,))

        result = cur.fetchone()

    except Exception as e:
        logger.exception(f"validate_previous_version_id: Unexpected error: {e}")
        abort(json_error(f"TSV file row# {row_i}: Problem encountered while validating previous_revision_hubmap_id", 500))
    
    if result is None:
            abort(json_error(f"TSV file row# {row_i}: previous_revision_hubmap_id '{previous_version_id}' does not exist", 406))
    elif result[0] is not None:
        abort(json_error(f"TSV file row# {row_i}: previous_version_id '{previous_version_id}' "
                            f"already has a newer version specified (next_revision_hubmap_id='{result[0]}')", 406))


def validate_uniprot_accession_numbers(row_i: int, uniprot_accession_numbers: str) -> None:
    for uniprot_accession_number in uniprot_accession_numbers.split(','):
        validate_uniprot_accession_number(row_i, uniprot_accession_number.strip())


def validate_uniprot_accession_number(row_i: int, uniprot_accession_number: str) -> None:
    response = None
    try:
        uniprot_url: str = f"https://www.uniprot.org/uniprot/{uniprot_accession_number}.rdf?include=yes"
        logger.debug(f'validate_uniprot_accession_number() URL: {uniprot_url}')
        response = requests.get(uniprot_url, headers={"Accept": "application/json"}, verify=False)
        # https://www.uniprot.org/help/api_retrieve_entries
        if response.status_code == 404:
            abort(json_error(f"TSV file row# {row_i}: Uniprot Accession Number"
                             f" '{uniprot_accession_number}' is not found in catalogue",
                             406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"TSV file row# {row_i}: Problem encountered validating Uniprot Accession Number", 406))
    finally:
        if response is not None:
            response.close()


def validate_orcids(row_i: int, orcids: str) -> None:
    for orcid in orcids.split(','):
        validate_orcid(row_i, orcid.strip())


def validate_orcid(row_i: int, orcid: str) -> None:
    """
    This field can be a single entry or a comma delimated list of ORCIDs.
    """
    response = None
    try:
        orcid_url: str = f"https://pub.orcid.org/{orcid}"
        logger.debug(f'validate_orcid() URL: {orcid_url}')
        response = requests.get(orcid_url, headers={"Accept": "application/json"}, verify=False)
        # TODO: 302
        if response.status_code == 404:
            abort(json_error(f"TSV file row# {row_i}: ORCID '{orcid}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"TSV file row# {row_i}: Problem encountered fetching ORCID", 406))
    finally:
        if response is not None:
            response.close()


def validate_rrid(row_i: int, rrid: str) -> None:
    response = None
    try:
        rrid_url: str = f"https://scicrunch.org/resolver/RRID:{rrid}.json"
        logger.debug(f'validate_rrid() URL: {rrid_url}')
        response = requests.get(rrid_url, headers={"Accept": "application/json"}, verify=False)
        if response.status_code != 200:
            abort(json_error(f"TSV file row# {row_i}: RRID '{rrid}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"TSV file row# {row_i}: Problem encountered validating RRID '{rrid}'", 406))
    finally:
        if response is not None:
            response.close()


def validate_dois(row_i: int, dois: str) -> None:
    for doi in dois.split(','):
        validate_doi(row_i, doi.strip())


def validate_doi(row_i: int, original_doi: str) -> None:
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
    response = None
    try:
        doi_url_base: str = "https://doi.org/api/handles/"
        canonicalize_doi = CanonicalizeDOI()
        doi: str = canonicalize_doi.canonicalize(original_doi)
        if doi is None:
            abort(json_error(
                f"TSV file row# {row_i}: DOI '{original_doi}' none of the prefixes {','.join(canonicalize_doi.valid())} matched", 406))
        doi_url: str = f"{doi_url_base}{quote(doi)}?type=URL"
        logger.debug(f'validate_doi() URL: {doi_url}')
        response = requests.get(doi_url, headers={"Accept": "application/json"}, verify=False)
        response_json: dict = response.json()
        if response.status_code != 200 or 'responseCode' not in response_json or response_json['responseCode'] != 1:
            abort(json_error(f"TSV file row# {row_i}: DOI '{original_doi}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"TSV file row# {row_i}: Problem encountered validating DOI '{original_doi}'", 406))
    finally:
        if response is not None:
            response.close()


def validate_hgncs(row_i: int, hgncs: str) -> None:
    for hgnc in hgncs.split(','):
        validate_hgnc(row_i, hgnc.strip())


def validate_hgnc(row_i: int, hgnc: str) -> None:
    """
    https://www.genenames.org/help/rest/
    Please only send REST requests at a rate of 10 requests per second
    If you experience 403 errors please contact us via our feedback form.

    Valid if 'response.numFound > 0'
    """
    response = None
    try:
        hgnc_url_base: str = "https://rest.genenames.org/fetch/hgnc_id/"
        hgnc_url: str = f"{hgnc_url_base}{hgnc}"
        logger.debug(f'validate_hgnc() URL: {hgnc_url}')
        response = requests.get(hgnc_url, headers={"Accept": "application/json"}, verify=False)
        response_json: dict = response.json()
        if 'response' not in response_json or 'numFound' not in response_json['response']:
            abort(json_error(f"TSV file row# {row_i}: Problem encountered validating HGNC '{hgnc}'", 406))
        num_found: int = response_json['response']['numFound']
        if response.status_code != 200 or num_found <= 0:
            abort(json_error(f"TSV file row# {row_i}: HGNC '{hgnc}' is not found in catalogue", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"TSV file row# {row_i}: Problem encountered validating HGNC '{hgnc}'", 406))
    finally:
        if response is not None:
            response.close()


def validate_uberon_id(row_i: int, ontology_id: str) -> None:
    required_prefix: str = "UBERON:"
    if ontology_id[0:len(required_prefix)] != required_prefix:
        abort(json_error(f"TSV file row# {row_i}: UBERON Ontoloty ID "
                         f"'{ontology_id}' must begin with '{required_prefix}'", 406))
    validate_ontology(row_i, ontology_id)



def validate_ontology(row_i: int, ontology_id: str) -> None:
    """
    https://www.ebi.ac.uk/ols/docs/api
    Ontology Search API

    ontology_id is a string of the form 'UBERON:0002113'.

    Valid if 'page.totalElements > 0'
    """
    response = None
    try:
        ols_url_base: str = "http://www.ebi.ac.uk/ols/api/terms"
        ols_url: str = f"{ols_url_base}?id={ontology_id}"
        logger.debug(f'validate_ontology() URL: {ols_url}')
        response = requests.get(ols_url, headers={"Accept": "application/json"}, verify=False, allow_redirects=True)
        if response.status_code != 200:
            abort(json_error(f"TSV file row# {row_i}: Ontology ID '{ontology_id}' is not found", 406))
    except requests.ConnectionError as error:
        # TODO: This should probably return a 502 and the frontend needs to be modified to handle it.
        abort(json_error(f"TSV file row# {row_i}: Problem encountered validating ontology_id '{ontology_id}'", 406))
    finally:
        if response is not None:
            response.close()


def validate_antibodytsv_row(row_i: int, row: dict, request_files: dict, ubkg_api_url: str, cur):
    """
    This routine will behave as follows.
    1) if any of the validation tests are found to fail it will throw an abort message with http status code,
    2) if all tests pass, it will return some data that it found while validating which would otherwise
    need to be looked up again.
    """
    logger.debug(f"validate_antibodytsv_row: row# {row_i}: {row}")

    validate_row_data(row_i, row)

    found_pdf: str = None
    if 'pdf' in request_files:
        for avr_pdf_file in request_files.getlist('pdf'):
            if avr_pdf_file.filename == row['avr_pdf_filename']:
                pdf_file_content: bytes = avr_pdf_file.stream.read()
                # Since this is a stream, we need to go back to the beginning or the next time that it is read
                # it will be read from the end where there are no characters providing an empty file.
                pdf_file_size_mb: float = len(pdf_file_content)/(1024.0*1000.0)
                max_ingest_file_upload_size_mb: float = 10.0
                if pdf_file_size_mb >= max_ingest_file_upload_size_mb:
                    abort(json_error(f"TSV file row# {row_i}: avr_pdf_filename '{row['avr_pdf_filename']}'"
                                     f" is over maximum file size of {max_ingest_file_upload_size_mb}MB", 406))
                avr_pdf_file.stream.seek(0)
                logger.debug("validate_antibodytsv_row: avr_pdf_file.filename:"
                             f" {row['avr_pdf_filename']}; size: {pdf_file_size_mb}MB")
                try:
                    # https://pypdf.readthedocs.io/en/stable/modules/PdfReader.html
                    PdfReader(io.BytesIO(pdf_file_content))
                    logger.debug("validate_antibodytsv_row: Processing"
                                 f" avr_pdf_filename: {avr_pdf_file.filename}; is a valid PDF file")
                    found_pdf = avr_pdf_file.filename
                    break
                except PdfReadError:
                    abort(json_error(f"TSV file row# {row_i}: avr_pdf_filename '{row['avr_pdf_filename']}'"
                                     " found, but not a valid PDF file", 406))
        if found_pdf is None:
            abort(json_error(f"TSV file row# {row_i}: avr_pdf_filename '{row['avr_pdf_filename']}' is not found", 406))
    else:
        abort(json_error(f"TSV file row# {row_i}: avr_pdf_filename '{row['avr_pdf_filename']}' is not found", 406))

    validate_previous_version_id(row_i, row['previous_version_id'], cur)
    # All of these make callouts to other RestAPIs...
    validate_uniprot_accession_numbers(row_i, row['uniprot_accession_number'])
    validate_hgncs(row_i, row['hgnc_id'])
    target_data: dict = validate_targets(row_i, row['target_symbol'], ubkg_api_url)
    validate_rrid(row_i, row['rrid'])
    validate_dois(row_i, row['protocol_doi'])
    validate_orcids(row_i, row['author_orcids'])
    validate_uberon_id(row_i, row['organ_uberon_id'])
    if row['manuscript_doi'] != '':
        validate_doi(row_i, row['manuscript_doi'])

    return found_pdf, target_data


def call_cedar_api(file_obj):
    cedar_url = current_app.config['CEDAR_VALIDATION_URL']
    # Reset stream just in case it was read earlier
    file_obj.stream.seek(0)
    files = {
        "input_file": (file_obj.filename, file_obj.stream)
    }
    try:
        response = requests.post(
            cedar_url,
            files=files
        )
        if not response.ok:
            abort(json_error(f"TSV Header Error: One or more key in TSV was invalid. Headers should be one of {', '.join(tsv_header_keys)}", 406))
        try:
            cedar_json = response.json()
        except Exception as e:
            abort(json_error(f"Error parsing resonse from Cedar: {e}", 500))
        if cedar_json.get("reporting"):
            error_strings = [
                f"Row {e['row']}, Column '{e['column']}': {e['value']} is invalid ({e['errorType']})"
                for e in cedar_json["reporting"]
            ]
    
            error_message = "Validation errors found:\n" + "\n".join(error_strings)
            
            abort(json_error(error_message, 400))
    except HTTPException:
        raise
    except Exception as e:
        abort(json_error(f"Spreadsheet Validator API request for {file_obj.filename} failed! Exception {e}", 500))

    return response

def validate_antibodytsv(request_files: dict, ubkg_api_url: str):
    """
    Used to validate the content of the uploaded .tsv file.

    Currently called from import_antibodies/__init__.py/import_antibodies()
    (endpoint implementation of '/antibodies/import', methods=['POST']).

    This routing will attempt to validate fields. Some fields can be looked up
    in alternate databases using MSAPI calls. In some cases it will try to validate
    the format of the data in the field, or in the case of a .pdf file it's validity
    as a .pdf file.

    It returns:
    1) A list of validated .pdf files (pdf_files_processed) that it has found in the .tsv file,
    2) A dictionary that maps the 'target_symbol' string given in the .tsv file to the
    'target_symbol' (i.e., approved name for the target from UBKG), and also 'target_aliases' for the
    'target_symbol' which is a list that contains strings that can be searched for this target
    (i.e, aliases, previous, approved).
    """
    start_time = time.time()
    pdf_files_processed: list = []
    target_datas: dict = {}

    with psycopg2.connect(
        host = current_app.config['DATABASE_HOST'],
        dbname = current_app.config['DATABASE_NAME'],
        user = current_app.config['DATABASE_USER'],
        password = current_app.config['DATABASE_PASSWORD']
    ) as conn:
        with conn.cursor() as cur:
            previous_version_ids = []
            for file in request_files.getlist('file'):
                if not file or file.filename == '':
                    abort(json_error('Filename missing in uploaded files', 406))
                if file and allowed_file(file.filename):
                    cedar_response = call_cedar_api(file)
                    file.stream.seek(0)
                    lines: [str] = [x.decode("ascii", "ignore") for x in file.stream.read().splitlines()]
                    file.stream.seek(0)
                    logger.debug(f'Lines: {lines}')
                    # TODO: Limit the number of lines to 16 (header plus 15 lines of data)
                    logger.debug(f"validate_antibodytsv: processing filename '{file.filename}'")
                    row_i = 1
                    for row_dr in csv.DictReader(lines, delimiter='\t'):
                        row = {k.lower().strip(): v.strip() for k, v in row_dr.items()}
                        if row['previous_version_id']:
                            if row['previous_version_id'] in previous_version_ids:
                                abort(json_error('Multiple rows contain the same value "previous_revision_hubmap_id". Each antibody may only have a single next revision', 406))
                            previous_version_ids.append(row['previous_version_id'])
                        row_i = row_i + 1
                        found_pdf, target_data = validate_antibodytsv_row(row_i, row, request_files, ubkg_api_url, cur)
                        if found_pdf is not None:
                            logger.debug(f"validate_antibodytsv: TSV file row# {row_i}:"
                                        f" found PDF file '{found_pdf}' as valid PDF")
                            pdf_files_processed.append(found_pdf)
                        target_datas |= target_data
                        # else:
                        #     logger.debug(f"validate_antibodytsv: TSV file row# {row_i}: valid PDF not found")
    logger.debug(f"validate_antibodytsv: found valid PDF files ({len(pdf_files_processed)}): '{pdf_files_processed}'")
    logger.debug(f"validate_antibodytsv: found target_datas ({len(target_datas)}): '{target_datas}'")
    logger.debug(f"validate_antibodytsv: run time: {datetime.timedelta(seconds=time.time() - start_time)}")
    return pdf_files_processed, target_datas


# TODO: Apparently a POST has a 100MB limit which we cannot check here.
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Allow testing the validation code through the command line.'
    )
    parser.add_argument('tsv_file',
                        help='The .tsv file used in the upload which may contain references to a .pdf file')
    parser.add_argument('pdf_file', nargs='*',
                        help='A .pdf file referenced in .tsv file. All lines should reference this file. IMPORTANT: The exact path must be used in the .tsv file!!!')
    args = parser.parse_args()

    # Since 'validate_antibodytsv' is intended to be called within a Flask App, we need to dummy one up here.
    from flask import Flask, request
    app = Flask(__name__)
    app.config.from_pyfile('../../../../instance/app.conf')
    data: dict = {
        'file': [open(args.tsv_file, 'rb')],
        'pdf': [open(pdf_file, 'rb') for pdf_file in args.pdf_file]
    }
    with app.test_request_context(method='POST',
                                  content_type='multipart/form-data',
                                  data=data):
        ubkg_api_url: str = app.config['UBKG_API_URL']

        start = time.time()
        pdf_files_processed, target_datas =\
            validate_antibodytsv(request.files, ubkg_api_url)
        end = time.time()
        print(f"pdf_files_processed ({len(pdf_files_processed)}): {pdf_files_processed}")
        print(f"target_datas ({len(target_datas)}): {target_datas}")
        print(f"Run time: {datetime.timedelta(seconds = end - start)}")
