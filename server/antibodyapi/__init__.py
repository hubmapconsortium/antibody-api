from flask import Flask, abort, jsonify, make_response, request, render_template
from werkzeug.exceptions import BadRequest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from . import default_config

def create_app(testing=False):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(default_config.DefaultConfig)
    if testing:
        app.config['TESTING'] = True
    else:
        # We should not load the gitignored app.conf during tests.
        app.config.from_pyfile('app.conf')

    @app.route('/')
    def hubmap():
        return render_template('pages/base.html', test_var="hello, world!")

    #Create the main driver function
    if __name__ == '__main__':
        #call the run method
        app.run()

    @app.route("/antibodies", methods=['POST'])
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
            abort(406)
        for prop in required_properties:
            if prop not in antibody:
                abort(406)

        conn = psycopg2.connect(
            dbname=app.config['DATABASE_NAME'],
            user=app.config['DATABASE_USER'],
            password=app.config['DATABASE_PASSWORD'],
            host=app.config['DATABASE_HOST']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        insert_query = '''
INSERT INTO antibodies (
    avr_url,
    protocols_io_doi,
    uniprot_accession_number,
    target_name,
    rrid,
    antibody_name,
    host_organism,
    clonality,
    vendor,
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
    %(vendor)s,
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
        cur.execute(insert_query, antibody)
        return make_response(jsonify(id=cur.fetchone()[0]), 201)
    return app
