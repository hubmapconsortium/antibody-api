import json
import random
import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from antibodyapi import create_app

@pytest.fixture(scope="session")
def flask_app():
    return create_app(testing=True)

@pytest.fixture(scope="session")
def client(flask_app):
    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            yield testing_client

@pytest.fixture
def mimetype():
    return 'application/json'

@pytest.fixture
def headers(mimetype):
    return {
        'Content-Type': mimetype,
        'Accepts': mimetype
    }

@pytest.fixture
def antibody_data(faker):
    return {
        'antibody': {
            'avr_url': faker.uri(),
            'protocols_io_doi': faker.uri(),
            'uniprot_accession_number': faker.uuid4(),
            'target_name': faker.first_name(),
            'rrid': 'AB_%s' % ('%s%s' % (faker.pyint(3333), faker.pyint(2222))),
            'antibody_name': faker.first_name(),
            'host_organism': faker.first_name(),
            'clonality': random.choice(('monoclonal','polyclonal')),
            'vendor': faker.first_name(),
            'catalog_number': faker.uuid4(),
            'lot_number': faker.uuid4(),
            'recombinant': faker.pybool(),
            'organ_or_tissue': faker.first_name(),
            'hubmap_platform': faker.first_name(),
            'submitter_orciid': faker.uuid4(),
            'created_by_user_displayname': faker.first_name(),
            'created_by_user_email': faker.ascii_email(),
            'created_by_user_sub': faker.last_name(),
            'group_uuid': faker.uuid4()
        }
    }

@pytest.fixture
def antibody_incomplete_data(antibody_data):
    del antibody_data['antibody'][random.choice(list(antibody_data['antibody'].keys()))]
    return antibody_data

@pytest.fixture(scope="session")
def conn(flask_app):
    conn = psycopg2.connect(
        dbname=flask_app.config['DATABASE_NAME'],
        user=flask_app.config['DATABASE_USER'],
        password=flask_app.config['DATABASE_PASSWORD'],
        host=flask_app.config['DATABASE_HOST']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    yield conn
    conn.close()

@pytest.fixture()
def cursor(conn):
    cur = conn.cursor()
    yield cur
    cur.execute('DELETE FROM antibodies')
    cur.close()

def test_post_with_no_body_should_return_400(client, headers):
    response = client.post('/antibodies', headers=headers)
    assert response.status == '400 BAD REQUEST'

def test_post_with_empty_json_body_should_return_406(client, headers):
    response = client.post('/antibodies', data=json.dumps({}), headers=headers)
    assert response.status == '406 NOT ACCEPTABLE'

def test_post_with_incomplete_json_body_should_return_406(
        client, headers, antibody_incomplete_data
    ):
    response = client.post(
        '/antibodies', data=json.dumps(antibody_incomplete_data), headers=headers
    )
    assert response.status == '406 NOT ACCEPTABLE'

class TestPostWithCompleteJSONBody:
    # pylint: disable=no-self-use,unused-argument
    @pytest.fixture
    def initial_antibodies_count(self, cursor):
        return self.get_antibodies_count(cursor)

    @pytest.fixture
    def final_antibodies_count(self, cursor):
        return self.get_antibodies_count(cursor)

    @pytest.fixture
    def last_antibody_id(self, cursor):
        cursor.execute('SELECT id FROM antibodies ORDER BY id DESC LIMIT 1')
        return cursor.fetchone()[0]

    @pytest.fixture
    def response(self, client, antibody_data, headers, initial_antibodies_count):
        return client.post('/antibodies', data=json.dumps(antibody_data), headers=headers)

    @pytest.fixture
    def last_antibody_data(self, ant_query, cursor, last_antibody_id):
        cursor.execute(ant_query, (last_antibody_id,))
        return cursor.fetchone()

    @pytest.fixture
    def ant_query(self):
        return '''
SELECT 
    avr_url, protocols_io_doi,
    uniprot_accession_number,
    target_name, rrid,
    antibody_name, host_organism,
    clonality, vendor,
    catalog_number, lot_number,
    recombinant, organ_or_tissue,
    hubmap_platform, submitter_orciid,
    created_by_user_displayname, created_by_user_email,
    created_by_user_sub, group_uuid
FROM antibodies WHERE id = %s
'''

    @classmethod
    def get_antibodies_count(cls, cursor):
        cursor.execute('SELECT COUNT(*) AS count FROM antibodies')
        return cursor.fetchone()[0]

    def test_should_return_a_201_response(self, response):
        assert response.status == '201 CREATED'

    def test_antibody_count_in_database_should_increase_by_one(
        self, initial_antibodies_count, response, final_antibodies_count
    ):
        assert (initial_antibodies_count + 1) == final_antibodies_count

    def test_api_should_return_created_id_in_json_format(
        self, response, last_antibody_id
    ):
        assert json.loads(response.data) == {'id': last_antibody_id}

    def test_all_antibody_fields_are_saved_correctly(
        self, response, antibody_data, last_antibody_data
    ):
        assert tuple(antibody_data['antibody'].values()) == last_antibody_data
