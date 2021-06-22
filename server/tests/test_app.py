import json
import pytest

def test_post_with_no_body_should_return_400(client, headers):
    response = client.post('/antibodies', headers=headers)
    assert response.status == '400 BAD REQUEST'

class TestGetAntibodies:
    # pylint: disable=no-self-use
    @pytest.fixture(autouse=True)
    def create_antibody(self, cursor, client, antibody_data, headers):
        client.post('/antibodies', data=json.dumps(antibody_data), headers=headers)
        yield
        cursor.execute('DELETE FROM antibodies')

    @pytest.fixture
    def response(self, client, headers):
        return client.get('/antibodies', headers=headers)

    def test_should_return_a_200_response(self, response):
        assert response.status == '200 OK'

    def test_all_antibody_fields_are_retrieved_correctly(
        self, response, antibody_data
    ):
        assert antibody_data['antibody'] == json.loads(response.data)['antibodies'][0]

class TestPostEmptyJSONBody:
    # pylint: disable=no-self-use
    @pytest.fixture
    def response(self, client, headers):
        return client.post(
            '/antibodies', data=json.dumps({}), headers=headers
        )

    def test_post_with_empty_json_body_should_return_406(self, response):
        assert response.status == '406 NOT ACCEPTABLE'

    def test_post_with_empty_json_should_return_error_message(self, response):
        assert json.loads(response.data) == {
            'message': 'Antibody missing'
        }

class TestPostIncompleteJSONBody:
    # pylint: disable=no-self-use
    @pytest.fixture
    def removed_field(self, antibody_incomplete_data):
        return antibody_incomplete_data[1]

    @pytest.fixture
    def incomplete_data(self, antibody_incomplete_data):
        return antibody_incomplete_data[0]

    @pytest.fixture
    def response(self, client, headers, incomplete_data):
        return client.post(
            '/antibodies', data=json.dumps(incomplete_data), headers=headers
        )

    def test_post_with_incomplete_json_body_should_return_406(
            self, response
        ):
        assert response.status == '406 NOT ACCEPTABLE'

    def test_post_with_incomplete_json_body_should_return_error_message(
            self, response, removed_field
        ):
        assert json.loads(response.data) == {
            'message': 'Antibody data incomplete: missing %s parameter' % removed_field
        }

class TestPostWithCompleteJSONBody:
    # pylint: disable=no-self-use,unused-argument
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

    @pytest.fixture
    def last_antibody_data(self, ant_query, cursor, last_antibody_id):
        cursor.execute(ant_query, (last_antibody_id,))
        return cursor.fetchone()

    @pytest.fixture
    def last_antibody_id(self, cursor):
        cursor.execute('SELECT id FROM antibodies ORDER BY id DESC LIMIT 1')
        return cursor.fetchone()[0]

    @pytest.fixture
    def initial_antibodies_count(self, cursor):
        return self.get_antibodies_count(cursor)

    @pytest.fixture
    def final_antibodies_count(self, cursor):
        return self.get_antibodies_count(cursor)

    @pytest.fixture
    def response(self, client, antibody_data, headers, initial_antibodies_count):
        return client.post('/antibodies', data=json.dumps(antibody_data), headers=headers)

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

    def test_if_antibody_fails_uniqueness_index_it_should_return_a_406_response(
        self, response, antibody_data, client, headers
    ):
        assert client.post(
            '/antibodies', data=json.dumps(antibody_data), headers=headers
        ).status == '406 NOT ACCEPTABLE'

    def test_if_antibody_fails_uniqueness_index_it_should_inform_it_in_message(
        self, response, antibody_data, client, headers
    ):
        assert json.loads(client.post(
            '/antibodies', data=json.dumps(antibody_data), headers=headers
        ).data) == {'message': 'Antibody not unique'}
