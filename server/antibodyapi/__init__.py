import csv
import os
import globus_sdk
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning # pylint: disable=import-error
from flask import (
    Flask, abort, g, jsonify, make_response, redirect,
    session, request, render_template, url_for
)
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
# pylint: disable=no-name-in-module
from psycopg2.errors import UniqueViolation
from antibodyapi.utils import (
    allowed_file, base_antibody_query, find_or_create_vendor, get_cursor,
    get_file_uuid, get_hubmap_uuid, get_user_info, insert_query,
    insert_query_with_avr_file_and_uuid, json_error
)

from . import default_config

UPLOAD_FOLDER = '/tmp'

requests.packages.urllib3.disable_warnings(category = InsecureRequestWarning) # pylint: disable=no-member

def create_app(testing=False):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(default_config.DefaultConfig)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    if testing:
        app.config['TESTING'] = True
    else:
        # We should not load the gitignored app.conf during tests.
        app.config.from_pyfile('app.conf')


    @app.route('/set_authenticated')
    def fake_is_auth():
        # remove this method when auth complete.
        session.update(is_authenticated=True)
        return redirect(url_for("hubmap"))

    @app.route('/')
    def hubmap():
        #replace by the correct way to check token validity.
        authenticated = session.get('is_authenticated')
        if not authenticated:
            return redirect(url_for('login'))

        return render_template('pages/base.html', test_var='hello, world!')

    @app.route('/antibodies/import', methods=['POST'])
    def import_antibodies(): # pylint: disable=too-many-branches
        authenticated = session.get('is_authenticated')
        if not authenticated:
            return redirect(url_for('login'))

        if 'file' not in request.files:
            abort(json_error('CSV file missing', 406))

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

    @app.route('/antibodies', methods=['GET'])
    def list_antibodies():
        cur = get_cursor(app)
        cur.execute(base_antibody_query() + ' ORDER BY a.id ASC')
        results = []
        for antibody in cur:
            ant = {
                'antibody_uuid': antibody[0],
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
          'submitter_orciid'
        )
        try:
            antibody = request.get_json()['antibody']
        except KeyError:
            abort(json_error('Antibody missing', 406))
        for prop in required_properties:
            if prop not in antibody:
                abort(json_error(
                    'Antibody data incomplete: missing %s parameter' % prop, 400
                    )
                )

        cur = get_cursor(app)
        antibody['vendor_id'] = find_or_create_vendor(cur, antibody['vendor'])
        del antibody['vendor']
        antibody['antibody_uuid'] = get_hubmap_uuid(app.config['UUID_API_URL'])
        antibody['created_by_user_displayname'] = session['name']
        antibody['created_by_user_email'] = session['email']
        antibody['created_by_user_sub'] = session['sub']
        antibody['group_uuid'] = '7e5d3aec-8a99-4902-ab45-f2e3335de8b4'
        try:
            cur.execute(insert_query(), antibody)
        except UniqueViolation:
            abort(json_error('Antibody not unique', 400))
        return make_response(jsonify(id=cur.fetchone()[0], uuid=antibody['antibody_uuid']), 201)

    @app.route('/login')
    def login():
        redirect_uri = url_for('login', _external=True)
        client = globus_sdk.ConfidentialAppAuthClient(
            app.config['APP_CLIENT_ID'],
            app.config['APP_CLIENT_SECRET']
        )
        client.oauth2_start_flow(redirect_uri)

        if 'code' not in request.args: # pylint: disable=no-else-return
            auth_uri = client.oauth2_get_authorize_url(query_params={"scope": "openid profile email urn:globus:auth:scope:transfer.api.globus.org:all urn:globus:auth:scope:auth.globus.org:view_identities urn:globus:auth:scope:nexus.api.globus.org:groups" }) # pylint: disable=line-too-long
            return redirect(auth_uri)
        else:
            code = request.args.get('code')
            tokens = client.oauth2_exchange_code_for_tokens(code)
            user_info = get_user_info(tokens)
            session.update(
                name=user_info['name'],
                email=user_info['email'],
                sub=user_info['sub'],
                tokens=tokens.by_resource_server,
                is_authenticated=True
            )
            return redirect(url_for('hubmap'))

    @app.route('/logout')
    def logout():
        """
        - Revoke the tokens with Globus Auth.
        - Destroy the session state.
        - Redirect the user to the Globus Auth logout page.
        """
        client = globus_sdk.ConfidentialAppAuthClient(
            app.config['APP_CLIENT_ID'],
            app.config['APP_CLIENT_SECRET']
        )

        # Revoke the tokens with Globus Auth
        if 'tokens' in session:
            for token in (token_info['access_token']
                for token_info in session['tokens'].values()):
                client.oauth2_revoke_token(token)

        # Destroy the session state
        session.clear()

        # build the logout URI with query params
        # there is no tool to help build this (yet!)
        redirect_uri = url_for('login', _external=True)

        globus_logout_url = (
            'https://auth.globus.org/v2/web/logout' +
            '?client={}'.format(app.config['APP_CLIENT_ID']) +
            '&redirect_uri={}'.format(redirect_uri) +
            '&redirect_name={}'.format('hubmap')
        )

        # Redirect the user to the Globus Auth logout page
        return redirect(globus_logout_url)


    @app.teardown_appcontext
    def close_db(error): # pylint: disable=unused-argument
        if 'connection' in g:
            g.connection.close()

    return app
