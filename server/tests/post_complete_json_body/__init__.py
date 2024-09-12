import json
import pytest
from antibody_testing import AntibodyTesting

class TestPostWithCompleteJSONBody(AntibodyTesting):
    # pylint: disable=no-self-use, unused-argument, too-many-arguments
    @pytest.fixture
    def add_vendor(self, cursor, antibody_data):
        cursor.execute(
            'INSERT INTO vendors (vendor_name) VALUES (%s)',
            (antibody_data['antibody']['vendor_name'],)
        )

    @pytest.fixture
    def add_vendor_uppercase(self, cursor, antibody_data):
        cursor.execute(
            'INSERT INTO vendors (vendor_name) VALUES (%s)',
            (antibody_data['antibody']['vendor_name'].upper(),)
        )

    @pytest.fixture
    def create_uuid_expectation(self, flask_app, headers, antibody_data):
        self.create_expectation(flask_app, headers, antibody_data['antibody'], 0)

    @pytest.fixture
    def response(
        self, client, antibody_data, headers, create_uuid_expectation, mocker
    ):
        with client.session_transaction() as sess:
            sess['is_authenticated'] = True
            sess['groups_access_token'] = 'woot'
            sess['name'] = 'Name'
            sess['email'] = 'name@example.com'
            sess['sub'] = '1234567890'
        data_to_send = {
            'antibody': { k: v for k, v in antibody_data['antibody'].items() if k[0] != '_' }
        }
        mocker.patch('elasticsearch.Elasticsearch')
        return client.post('/antibodies', data=json.dumps(data_to_send), headers=headers)

    def test_antibody_gets_uuid_saved(
        self, response, antibody_data, last_antibody_uuid
    ):
        """POST /antibodies with a full JSON body should save a UUID for the new antibody"""
        assert antibody_data['antibody']['_antibody_uuid'] == last_antibody_uuid

    def test_should_return_a_201_response(self, response):
        """POST /antibodies with a full JSON body should return 201 CREATED"""
        assert response.status == '201 CREATED'

    def test_antibody_count_in_database_should_increase_by_one(
        self, initial_antibodies_count, response, final_antibodies_count
    ):
        """POST /antibodies with a full JSON body should increase antibody count by one"""
        assert (initial_antibodies_count + 1) == final_antibodies_count

    def test_api_should_return_created_id_in_json_format(
        self, response, last_antibody_id, last_antibody_uuid
    ):
        """POST /antibodies with a full JSON body should return id in JSON format"""
        assert json.loads(response.data) == {'id': last_antibody_id, 'uuid': last_antibody_uuid}

    def test_all_antibody_fields_are_saved_correctly(
        self, response, antibody_data, last_antibody_data
    ):
        """POST /antibodies with a full JSON body should save all fields correctly"""
        sent_data = { k: v for k, v in antibody_data['antibody'].items() if k[0] != '_' }
        additional_fields = (
            'Name',
            'name@example.com',
            '1234567890',
            '7e5d3aec-8a99-4902-ab45-f2e3335de8b4'
        )
        expected_data = tuple(sent_data.values()) + additional_fields
        assert expected_data == last_antibody_data

    def test_api_should_create_a_new_vendor_if_it_does_not_exist_already(
        self, initial_vendor_count, response, final_vendor_count
    ):
        """POST /antibodies should create a new vendor if it does not exist already"""
        assert (initial_vendor_count + 1) == final_vendor_count

    def test_api_should_save_new_vendor_correctly(
        self, response, antibody_data, last_vendor_data
    ):
        """POST /antibodies should save a new vendor correctly"""
        assert antibody_data['antibody']['vendor_name'] == last_vendor_data

    def test_api_should_not_create_vendor_if_it_exists_already(
        self, add_vendor, initial_vendor_count, response, final_vendor_count
    ):
        """POST /antibodies should not create a new vendor if it already exists"""
        assert initial_vendor_count == final_vendor_count

    def test_api_should_identify_vendor_regardless_of_case(
        self, add_vendor_uppercase, initial_vendor_count, response, final_vendor_count
    ):
        """POST /antibodies should identify an existing vendor regardless of case"""
        assert initial_vendor_count == final_vendor_count
