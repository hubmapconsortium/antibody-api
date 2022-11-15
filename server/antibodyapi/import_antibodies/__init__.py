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
from antibodyapi.utils.validation import validate_antibodycsv
from antibodyapi.utils.elasticsearch import index_antibody
import string
import logging


import_antibodies_blueprint = Blueprint('import_antibodies', __name__)

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def only_printable(s: str) -> str:
    # This does not work because (apparently) the TM symbol is a unicode character.
    # s.encode('utf-8', errors='ignore').decode('utf-8')
    # So, we use the more restrictive string.printable which does not contain unicode characters.
    return ''.join(c for c in s if c in string.printable)


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
                    # silently drop any non-printable characters like Trademark symbols from Excel documents
                    logger.info(f'row: {row}')
                    row = [only_printable(i) for i in row]
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
                    # do an auto lower case on anything is 'true' or 'false' as Excel likes
                    # all uppercase and people seem to use Excel to make the .csv files
                    row['recombinant'] = row['recombinant'].lower()
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
                                    row['avr_filename'] = secure_filename(row['avr_filename'])
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
