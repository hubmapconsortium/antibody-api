import csv
import os
from flask import (
    abort, Blueprint, current_app, jsonify, make_response,
    redirect, request, session, url_for, render_template
)
from psycopg2.errors import UniqueViolation #pylint: disable=no-name-in-module
from werkzeug.utils import secure_filename
from antibodyapi.utils import (
    allowed_file, find_or_create_vendor, get_cursor,
    get_file_uuid, get_group_id, get_hubmap_uuid,
    insert_query, insert_query_with_avr_file_and_uuid,
    json_error
)
from antibodyapi.utils.validation import validate_antibodycsv, CanonicalizeYNResponse, CanonicalizeDOI
from antibodyapi.utils.elasticsearch import index_antibody
from typing import List
import string
import logging

import_antibodies_blueprint = Blueprint('import_antibodies', __name__)
logger = logging.getLogger(__name__)


def only_printable_and_strip(s: str) -> str:
    # This does not work because (apparently) the TM symbol is a unicode character.
    # s.encode('utf-8', errors='ignore').decode('utf-8')
    # So, we use the more restrictive string.printable which does not contain unicode characters.
    return ''.join(c for c in s if c in string.printable).strip()


@import_antibodies_blueprint.route('/antibodies/import', methods=['POST'])
def import_antibodies(): # pylint: disable=too-many-branches
    """
    Currently this is called from 'server/antibodyapi/hubmap/templates/base.html' through the
    <form onsubmit="AJAXSubmit(this);..." enctype="..." action="/antibodies/import" method="post" ...>

    NOTE: The maximum .pdf size is currently 10Mb.
    """
    if not session.get('is_authenticated'):
        return redirect(url_for('login'))

    if not session.get('is_authorized'):
        logger.info("User is not authorized.")
        hubmap_avr_uploaders_group_id: str = current_app.config['HUBMAP_AVR_UPLOADERS_GROUP_ID']
        return render_template(
            'unauthorized.html',
            hubmap_avr_uploaders_group_id=hubmap_avr_uploaders_group_id
        )

    if 'file' not in request.files:
        abort(json_error('CSV file missing', 406))

    app = current_app
    cur = get_cursor(app)
    uuids_and_names = []

    group_id = get_group_id(app.config['INGEST_API_URL'], request.form.get('group_id'))
    if group_id is None:
        abort(json_error('Not a member of a data provider group or no group_id provided', 406))

    # Validate everything before saving anything...
    pdf_files_processed, target_datas =\
        validate_antibodycsv(request.files, app.config['UBKG_API_URL'])

    for file in request.files.getlist('file'):
        if file and allowed_file(file.filename):
            filename: str = secure_filename(file.filename)
            logger.info(f"import_antibodies: processing filename: {filename}")
            file_path: bytes = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            with open(file_path, encoding="ascii", errors="ignore") as csvfile:
                row_i: int = 1
                for row_dr in csv.DictReader(csvfile, delimiter=','):
                    # silently drop any non-printable characters like Trademark symbols from Excel documents
                    # and make all the keys lowercase so comparison is easy...
                    row = {k.lower(): only_printable_and_strip(v) for (k, v) in row_dr.items()}
                    row_i += 1
                    try:
                        row['vendor_id'] = find_or_create_vendor(cur, row['vendor'])
                    except KeyError:
                        abort(json_error(f"CSV file row# {row_i}: Problem processing Vendor field", 406))
                    vendor_name: str = row['vendor']
                    del row['vendor']
                    # The .csv file contains a 'target_symbol' field that is (possibly) resolved into a different
                    # 'target_symbol' by the UBKG lookup during validation. Here, whatever the user entered is
                    # replaced by the 'target_symbol' returned by UBKG.
                    target_symbol_from_csv: str = row['target_symbol']
                    row['target_symbol'] = target_datas[target_symbol_from_csv]['target_symbol']
                    # The target_aliases is a list of the other symbols that are associated with the target_symbol,
                    # and it gets saved to ElasticSearch, but not the database.
                    target_aliases: List[str] = target_datas[target_symbol_from_csv]['target_aliases']
                    hubmap_uuid_dict: dict = get_hubmap_uuid(app.config['UUID_API_URL'])
                    row['antibody_uuid'] = hubmap_uuid_dict.get('uuid')
                    row['antibody_hubmap_id'] = hubmap_uuid_dict.get('hubmap_id')
                    row['created_by_user_displayname'] = session['name']
                    row['created_by_user_email'] = session['email']
                    row['created_by_user_sub'] = session['sub']
                    row['group_uuid'] = group_id

                    # Canonicalize entries that we can so that they are always saved under the same string...
                    row['clonality'] = row['clonality'].lower()
                    row['host'] = row['host'].capitalize()
                    row['organ'] = row['organ'].lower()
                    # NOTE: The validation step will try to canonicalize and if it can't throw an error.
                    # So, by the time that we get here canonicalize will return a string.
                    canonicalize_yn_response = CanonicalizeYNResponse()
                    row['recombinant'] = canonicalize_yn_response.canonicalize(row['recombinant'])
                    canonicalize_doi = CanonicalizeDOI()
                    row['protocol_doi'] = canonicalize_doi.canonicalize_multiple(row['protocol_doi'])
                    if row['manuscript_doi'] != '':
                        row['manuscript_doi'] = canonicalize_doi.canonicalize(row['manuscript_doi'])

                    query = insert_query()
                    if 'avr_pdf_filename' in row.keys():
                        if 'pdf' in request.files:
                            for avr_file in request.files.getlist('pdf'):
                                if avr_file.filename == row['avr_pdf_filename']:
                                    row['avr_pdf_uuid'] = get_file_uuid(
                                        app.config['INGEST_API_URL'],
                                        app.config['UPLOAD_FOLDER'],
                                        row['antibody_uuid'],
                                        avr_file
                                    )
                                    query = insert_query_with_avr_file_and_uuid()
                                    row['avr_pdf_filename'] = secure_filename(row['avr_pdf_filename'])
                    try:
                        logger.debug(f"import_antibodies: SQL inserting row: {row}")
                        cur.execute(query, row)
                        logger.debug(f"import_antibodies: SQL inserting row SUCCESS!")
                        uuids_and_names.append({
                            'antibody_uuid': row['antibody_uuid']
                        })
                        index_antibody(row | {'vendor_name': vendor_name, 'target_aliases': target_aliases})
                    except KeyError as ke:
                        abort(json_error(f'CSV file row# {row_i}; key error: {ke}.', 406))
                    except UniqueViolation:
                        abort(json_error(f"CSV file row# {row_i}: Antibody not unique", 406))
        else:
            abort(json_error('Filetype forbidden', 406))

    pdf_files_not_processed: list = []
    for avr_file in request.files.getlist('pdf'):
        if avr_file.filename not in pdf_files_processed:
            pdf_files_not_processed.append(avr_file.filename)
    return make_response(jsonify(antibodies=uuids_and_names, pdf_files_not_processed=pdf_files_not_processed), 201)
