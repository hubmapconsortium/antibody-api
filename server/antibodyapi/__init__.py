import csv
import os
from flask import Flask, abort, jsonify, make_response, request, render_template
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
# pylint: disable=no-name-in-module
from psycopg2.errors import UniqueViolation
from . import default_config

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def base_antibody_query():
    return '''
SELECT
    a.avr_url, a.protocols_io_doi,
    a.uniprot_accession_number,
    a.target_name, a.rrid,
    a.antibody_name, a.host_organism,
    a.clonality, v.name,
    a.catalog_number, a.lot_number,
    a.recombinant, a.organ_or_tissue,
    a.hubmap_platform, a.submitter_orciid,
    a.created_by_user_displayname, a.created_by_user_email,
    a.created_by_user_sub, a.group_uuid
FROM antibodies a
JOIN vendors v ON a.vendor_id = v.id
'''

def insert_query():
    return '''
INSERT INTO antibodies (
    avr_url,
    protocols_io_doi,
    uniprot_accession_number,
    target_name,
    rrid,
    antibody_name,
    host_organism,
    clonality,
    vendor_id,
    catalog_number,
    lot_number,
    recombinant,
    organ_or_tissue,
    hubmap_platform,
    submitter_orciid,
    created_timestamp,
    created_by_user_displayname,
    created_by_user_email,
    created_by_user_sub,
    group_uuid
) 
VALUES (
    %(avr_url)s,
    %(protocols_io_doi)s,
    %(uniprot_accession_number)s,
    %(target_name)s,
    %(rrid)s,
    %(antibody_name)s,
    %(host_organism)s,
    %(clonality)s,
    %(vendor_id)s,
    %(catalog_number)s,
    %(lot_number)s,
    %(recombinant)s,
    %(organ_or_tissue)s,
    %(hubmap_platform)s,
    %(submitter_orciid)s,
    EXTRACT(epoch FROM NOW()),
    %(created_by_user_displayname)s,
    %(created_by_user_email)s,
    %(created_by_user_sub)s,
    %(group_uuid)s
) RETURNING id
'''

def create_app(testing=False):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(default_config.DefaultConfig)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    if testing:
        app.config['TESTING'] = True
    else:
        # We should not load the gitignored app.conf during tests.
        app.config.from_pyfile('app.conf')

    @app.route('/')
    def hubmap():
        return render_template('pages/base.html', test_var='hello, world!')

    @app.route('/antibodies/import', methods=['POST'])
    def import_antibodies():
        if 'file' not in request.files:
            abort(json_error('CSV file missing', 406))
        file = request.files['file']
        if file.filename == '':
            abort(json_error('Filename missing', 406))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename)) as csvfile:
                antibodycsv = csv.DictReader(csvfile, delimiter=',')
                conn = psycopg2.connect(
                    dbname=app.config['DATABASE_NAME'],
                    user=app.config['DATABASE_USER'],
                    password=app.config['DATABASE_PASSWORD'],
                    host=app.config['DATABASE_HOST']
                )
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                cur = conn.cursor()
                for row in antibodycsv:
                    try:
                        row['vendor_id'] = find_or_create_vendor(cur, row['vendor'])
                    except KeyError:
                        abort(json_error('CSV fields are wrong', 406))
                    del row['vendor']
                    try:
                        cur.execute(insert_query(), row)
                    except KeyError:
                        abort(json_error('CSV fields are wrong', 406))
                    except UniqueViolation:
                        abort(json_error('Antibody not unique', 406))
        else:
            abort(json_error('Filetype forbidden', 406))
        return ('', 204)

    @app.route('/antibodies', methods=['GET'])
    def list_antibodies():
        conn = psycopg2.connect(
            dbname=app.config['DATABASE_NAME'],
            user=app.config['DATABASE_USER'],
            password=app.config['DATABASE_PASSWORD'],
            host=app.config['DATABASE_HOST']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(base_antibody_query() + ' ORDER BY a.id ASC')
        results = []
        for antibody in cur:
            ant = {
                'avr_url': antibody[0],
                'protocols_io_doi': antibody[1],
                'uniprot_accession_number': antibody[2],
                'target_name': antibody[3],
                'rrid': antibody[4],
                'antibody_name': antibody[5],
                'host_organism': antibody[6],
                'clonality': antibody[7],
                'vendor': antibody[8],
                'catalog_number': antibody[9],
                'lot_number': antibody[10],
                'recombinant': antibody[11],
                'organ_or_tissue': antibody[12],
                'hubmap_platform': antibody[13],
                'submitter_orciid': antibody[14],
                'created_by_user_displayname': antibody[15],
                'created_by_user_email': antibody[16],
                'created_by_user_sub': antibody[17],
                'group_uuid': antibody[18]
            }
            results.append(ant)
        return make_response(jsonify(antibodies=results), 200)

    @app.route('/antibodies', methods=['POST'])
    def save_antibody():
        required_properties = (
          'avr_url',
          'protocols_io_doi',
          'uniprot_accession_number',
          'target_name',
          'rrid',
          'antibody_name',
          'host_organism',
          'clonality',
          'vendor',
          'catalog_number',
          'lot_number',
          'recombinant',
          'organ_or_tissue',
          'hubmap_platform',
          'submitter_orciid',
          'created_by_user_displayname',
          'created_by_user_email',
          'created_by_user_sub',
          'group_uuid'
        )
        try:
            antibody = request.get_json()['antibody']
        except KeyError:
            abort(json_error('Antibody missing', 406))
        for prop in required_properties:
            if prop not in antibody:
                abort(json_error(
                    'Antibody data incomplete: missing %s parameter' % prop, 406
                    )
                )

        conn = psycopg2.connect(
            dbname=app.config['DATABASE_NAME'],
            user=app.config['DATABASE_USER'],
            password=app.config['DATABASE_PASSWORD'],
            host=app.config['DATABASE_HOST']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        antibody['vendor_id'] = find_or_create_vendor(cur, antibody['vendor'])
        del antibody['vendor']
        try:
            cur.execute(insert_query(), antibody)
        except UniqueViolation:
            abort(json_error('Antibody not unique', 406))
        return make_response(jsonify(id=cur.fetchone()[0]), 201)
    return app

def json_error(message, error_code):
    return make_response(jsonify(message=message), error_code)

def find_or_create_vendor(cursor, name):
    cursor.execute('SELECT id FROM vendors WHERE name = %s', (name,))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        cursor.execute('INSERT INTO vendors (name) VALUES (%s) RETURNING id', (name,))
        return cursor.fetchone()[0]
