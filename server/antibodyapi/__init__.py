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

from antibodyapi.hubmap import hubmap_blueprint
from antibodyapi.import_antibodies import import_antibodies_blueprint
from antibodyapi.list_antibodies import list_antibodies_blueprint
from antibodyapi.login import login_blueprint
from antibodyapi.save_antibody import save_antibody_blueprint

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

    app.register_blueprint(hubmap_blueprint)
    app.register_blueprint(import_antibodies_blueprint)
    app.register_blueprint(list_antibodies_blueprint)
    app.register_blueprint(login_blueprint)
    app.register_blueprint(save_antibody_blueprint)

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
        redirect_uri = url_for('login.login', _external=True)

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
