import csv
import os
from flask import (
    abort, Blueprint, current_app, jsonify, make_response,
    redirect, request, session, url_for, render_template
)
import psycopg2
from psycopg2._psycopg import connection
from psycopg2.errors import UniqueViolation #pylint: disable=no-name-in-module
from werkzeug.utils import secure_filename
from antibodyapi.utils import (
    allowed_file, find_or_create_vendor, get_cursor,
    get_file_uuid, get_group_id, get_hubmap_uuid,
    insert_query, insert_query_with_avr_file_and_uuid,
    json_error, update_next_version_query, fetch_previous_version_pdf_uuid_query
)
from antibodyapi.utils.elasticsearch import update_next_version_es
from antibodyapi.utils.validation import validate_antibodytsv, CanonicalizeYNResponse, CanonicalizeDOI
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
        abort(json_error('TSV file missing', 406))

    app = current_app
    cur = get_cursor(app)
    hubmap_ids_and_names = []

    group_id = get_group_id(app.config['INGEST_API_URL'], request.form.get('group_id'))
    if group_id is None:
        abort(json_error('Not a member of a data provider group or no group_id provided', 406))

    # Validate everything before saving anything...
    pdf_files_processed, target_datas =\
        validate_antibodytsv(request.files, app.config['UBKG_API_URL'])
    
    conn = psycopg2.connect(
        host=app.config['DATABASE_HOST'],
        user=app.config['DATABASE_USER'],
        dbname=app.config['DATABASE_NAME'],
        password=app.config['DATABASE_PASSWORD']
    )
    conn.autocommit = False

    try:
        with conn:
            cur = conn.cursor()
            for file in request.files.getlist('file'):
                if not (file and allowed_file(file.filename)):
                    raise Exception('Incorrect File Type. TSV and PDF files required.')
                filename: str = secure_filename(file.filename)
                logger.info(f"import_antibodies: processing filename: {filename}")
                file_path: bytes = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                with open(file_path, encoding="ascii", errors="ignore") as tsvfile:
                    row_i: int = 1
                    for row_dr in csv.DictReader(tsvfile, delimiter='\t'):
                        # silently drop any non-printable characters like Trademark symbols from Excel documents
                        # and make all the keys lowercase so comparison is easy...
                        row = {k.lower(): only_printable_and_strip(v) for (k, v) in row_dr.items()}
                        row_i += 1
                        try:
                            row['vendor_id'] = find_or_create_vendor(cur, row['vendor'])
                        except KeyError:
                            abort(json_error(f"TSV file row# {row_i}: Problem processing Vendor field", 406))
                        # Save this for index_antibody() Elasticsearch, but remove from for DB store...
                        vendor_name: str = row['vendor']
                        del row['vendor']
                        # The .tsv file contains a 'target_symbol' field that is (possibly) resolved into a different
                        # 'target_symbol' by the UBKG lookup during validation. Here, whatever the user entered is
                        # replaced by the 'target_symbol' returned by UBKG.
                        target_symbol_from_tsv: str = row['target_symbol']
                        row['target_symbol'] = target_datas[target_symbol_from_tsv]['target_symbol']
                        # The target_aliases is a list of the other symbols that are associated with the target_symbol,
                        # and it gets saved to ElasticSearch, but not the database.
                        target_aliases: List[str] = target_datas[target_symbol_from_tsv]['target_aliases']
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
                        
                        previous_pdf = fetch_previous_version_pdf_uuid_query()
                        cur.execute(previous_pdf, {'previous_version_id': row['previous_version_id']})
                        prev_result = cur.fetchone()            
                        if prev_result:
                            row['previous_version_pdf_uuid'] = prev_result[0]
                            row['previous_version_pdf_filename'] = prev_result[1]
                        else:
                            row['previous_version_pdf_uuid'] = None
                            row['previous_version_pdf_filename'] = None
                        row['next_version_id'] = None
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
                        
                        logger.debug(f"import_antibodies: SQL inserting row: {row}")
                        cur.execute(query, row)
                        logger.debug(f"import_antibodies: SQL inserting row SUCCESS!")
                        hubmap_ids_and_names.append({
                            'antibody_hubmap_id': row['antibody_hubmap_id'],
                            'antibody_name': row.get('avr_pdf_filename')
                        })
                        try:
                            index_antibody(row | {'vendor_name': vendor_name, 'target_aliases': target_aliases})
                        except Exception as index_err:
                            logger.debug(f"Elasticsearch indexing failed on row {row_i}: {index_err}")
                            raise Exception("We couldn’t complete your request due to a system error. Your data has not been saved. Please try again in a few minutes. If the problem continues, contact support.")
                        if row['previous_version_id']:
                            update_query = update_next_version_query()
                            cur.execute(update_query, {
                                'next_version_id': row['antibody_hubmap_id'],
                                'previous_version_id': row['previous_version_id']
                            })
                            try:
                                update_next_version_es(row['previous_version_id'], row['antibody_hubmap_id'])
                            except Exception as index_err:
                                logger.debug(f"Elasticsearch indexing failed on {row_i} updating next_version_id")
            cur.close()
    except Exception as e:
        conn.rollback()
        conn.close()
        abort(json_error(str(e), 500))
    finally:
        if not conn.closed:
            conn.close()
    pdf_files_not_processed: list = []
    for avr_file in request.files.getlist('pdf'):
        if avr_file.filename not in pdf_files_processed:
            pdf_files_not_processed.append(avr_file.filename)
    return make_response(jsonify(antibodies=hubmap_ids_and_names, pdf_files_not_processed=pdf_files_not_processed), 201)
