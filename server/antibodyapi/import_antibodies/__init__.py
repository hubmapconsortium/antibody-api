import csv
import os
from flask import (
    abort, Blueprint, current_app, jsonify, make_response,
    redirect, request, session
)
from antibodyapi.utils import (
    allowed_file, base_antibody_query, find_or_create_vendor, get_cursor,
    get_file_uuid, get_hubmap_uuid, get_user_info, insert_query,
    insert_query_with_avr_file_and_uuid, json_error
)
from psycopg2.errors import UniqueViolation
from werkzeug.utils import secure_filename

import_antibodies_blueprint = Blueprint('import_antibodies', __name__)
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

    for file in request.files.getlist('file'):
        if file.filename == '':
            abort(json_error('Filename missing', 406))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename)) as csvfile:
                antibodycsv = csv.DictReader(csvfile, delimiter=',')
                for row in antibodycsv:
                    try:
                        row['vendor_id'] = find_or_create_vendor(cur, row['vendor'])
                    except KeyError:
                        abort(json_error('CSV fields are wrong', 406))
                    del row['vendor']
                    row['antibody_uuid'] = get_hubmap_uuid(app.config['UUID_API_URL'])
                    row['created_by_user_displayname'] = session['name']
                    row['created_by_user_email'] = session['email']
                    row['created_by_user_sub'] = session['sub']
                    row['group_uuid'] = '7e5d3aec-8a99-4902-ab45-f2e3335de8b4'
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
                    except KeyError:
                        abort(json_error('CSV fields are wrong', 406))
                    except UniqueViolation:
                        abort(json_error('Antibody not unique', 406))
        else:
            abort(json_error('Filetype forbidden', 406))
    return make_response(jsonify(antibodies=uuids_and_names), 201)
