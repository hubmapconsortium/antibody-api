from flask import Flask, abort, jsonify, make_response, request
from werkzeug.exceptions import BadRequest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_app(testing=False):
    app = Flask(__name__)

    if testing:
        app.config['TESTING'] = True

    def database_name():
        if app.config['TESTING']:
            return 'antibodydb_test'
        return 'antibodydb'

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
          'created_timestamp',
          'created_by_user_displayname',
          'created_by_user_email',
          'created_by_user_sub',
          'group_uuid'
        )
        try:
            antibody = request.get_json()['antibody']
        except BadRequest:
            abort(406)
        for prop in required_properties:
            if prop not in antibody:
                abort(406)

        conn = psycopg2.connect(
            dbname=database_name(),
            user='postgres',
            password='password',
            host='db'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        insert_query = '''
INSERT INTO antibodies (avr_url,protocols_io_doi,uniprot_accession_number,target_name,rrid,antibody_name,host_organism,clonality,vendor,catalog_number,lot_number,recombinant,organ_or_tissue,hubmap_platform,submitter_orciid,created_timestamp,created_by_user_displayname,created_by_user_email,created_by_user_sub,group_uuid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        '''
        insert_fields = (
            antibody['avr_url'],
            antibody['protocols_io_doi'],
            antibody['uniprot_accession_number'],
            antibody['target_name'],
            antibody['rrid'],
            antibody['antibody_name'],
            antibody['host_organism'],
            antibody['clonality'],
            antibody['vendor'],
            antibody['catalog_number'],
            antibody['lot_number'],
            antibody['recombinant'],
            antibody['organ_or_tissue'],
            antibody['hubmap_platform'],
            antibody['submitter_orciid'],
            antibody['created_timestamp'],
            antibody['created_by_user_displayname'],
            antibody['created_by_user_email'],
            antibody['created_by_user_sub'],
            antibody['group_uuid']
        )
        cur.execute(insert_query, insert_fields)
        return make_response(jsonify(id=cur.fetchone()[0]), 201)
    return app
