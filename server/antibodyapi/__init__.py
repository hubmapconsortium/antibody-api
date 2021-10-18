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
from antibodyapi.logout import logout_blueprint
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
    app.register_blueprint(logout_blueprint)
    app.register_blueprint(save_antibody_blueprint)

    @app.teardown_appcontext
    def close_db(error): # pylint: disable=unused-argument
        if 'connection' in g:
            g.connection.close()

    return app
