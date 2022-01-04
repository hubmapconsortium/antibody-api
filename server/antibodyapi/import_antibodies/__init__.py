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
                for row in antibodycsv:
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
