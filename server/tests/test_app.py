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
            'created_timestamp': faker.unix_time(),
            'created_by_user_displayname': faker.first_name(),
            'created_by_user_email': faker.ascii_email(),
            'created_by_user_sub': faker.last_name(),
            'group_uuid': faker.uuid4()
        }
    }

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

@pytest.fixture(scope="session")
def cursor(conn):
    cur = conn.cursor()
    yield cur
    cur.execute('DELETE FROM antibodies')
    cur.close()

def get_antibodies_count(cursor):
    cursor.execute('SELECT COUNT(*) AS count FROM antibodies')
    return cursor.fetchone()[0]

def get_last_antibody_id(cursor):
    cursor.execute('SELECT id FROM antibodies ORDER BY id DESC LIMIT 1')
    return cursor.fetchone()[0]

def test_post_antibody(client, headers, antibody_data, cursor):
    antibodies_count = get_antibodies_count(cursor)
    response = client.post('/antibodies', data=json.dumps(antibody_data), headers=headers)

    assert response.status == '201 CREATED'

    new_antibodies_count = get_antibodies_count(cursor)
    assert (new_antibodies_count-antibodies_count) == 1

    assert json.loads(response.data) == {'id': get_last_antibody_id(cursor)}

def test_post_empty_antibody(client, headers):
    response = client.post('/antibodies', headers=headers)
    assert response.status == '406 NOT ACCEPTABLE'
