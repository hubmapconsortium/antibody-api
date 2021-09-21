import random
import psycopg2
import pytest
from faker import Faker
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from antibodyapi import create_app

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call): # pylint: disable=unused-argument
    outcome = yield
    report = outcome.get_result()

    test_fn = item.obj
    docstring = getattr(test_fn, '__doc__')
    if docstring:
        report.nodeid = docstring

def raw_antibody_data():
    faker = Faker()
    return {
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

@pytest.fixture(scope='class')
def antibody_data():
    return {
        'antibody': raw_antibody_data()
    }

@pytest.fixture(scope='class')
def antibody_data_multiple():
    antibodies = []
    for _ in range(random.randint(2,8)):
        antibodies.append(raw_antibody_data())
    return {'antibody': antibodies}

@pytest.fixture(scope='class')
def antibody_incomplete_data(antibody_data):
    removed_field = random.choice(list(antibody_data['antibody'].keys()))
    del antibody_data['antibody'][removed_field]
    return (antibody_data, removed_field)

@pytest.fixture(scope='session')
def client(flask_app):
    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            yield testing_client

@pytest.fixture(scope='session')
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
    cur.execute('DELETE FROM vendors')
    cur.close()

@pytest.fixture(scope='session')
def flask_app():
    return create_app(testing=True)

@pytest.fixture(scope='session')
def headers(mimetype):
    return {
        'Content-Type': mimetype,
        'Accept': mimetype
    }

@pytest.fixture(scope='session')
def mimetype():
    return 'application/json'
