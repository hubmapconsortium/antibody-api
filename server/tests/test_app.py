import json
import random
import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from antibodyapi import create_app

@pytest.fixture(scope="session")
def client():
    flask_app = create_app(testing=True)
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
def conn():
    conn = psycopg2.connect(
        dbname='antibodydb_test',
        user='postgres',
        password='password',
        host='db'
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
    def response(self, client, antibody_data, headers, initial_antibodies_count):
        return client.post('/antibodies', data=json.dumps(antibody_data), headers=headers)

    @classmethod
    def get_antibodies_count(cls, cursor):
        cursor.execute('SELECT COUNT(*) AS count FROM antibodies')
        return cursor.fetchone()[0]

    @classmethod
    def get_last_antibody_id(cls, cursor):
        cursor.execute('SELECT id FROM antibodies ORDER BY id DESC LIMIT 1')
        return cursor.fetchone()[0]

    def test_should_return_a_201_response(self, response):
        assert response.status == '201 CREATED'

    def test_antibody_count_in_database_should_increase_by_one(
        self, initial_antibodies_count, cursor, response
    ):
        assert (initial_antibodies_count + 1) == self.get_antibodies_count(cursor)

    def test_api_should_return_created_id_in_json_format(self, cursor, response):
        assert json.loads(response.data) == {'id': self.get_last_antibody_id(cursor)}
