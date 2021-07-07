import io
import json
import pytest

def base_antibody_query():
    return '''
SELECT 
    a.avr_url, a.protocols_io_doi,
    a.uniprot_accession_number,
    a.target_name, a.rrid,
    a.antibody_name, a.host_organism,
    a.clonality, v.name,
    a.catalog_number, a.lot_number,
    a.recombinant, a.organ_or_tissue,
    a.hubmap_platform, a.submitter_orciid,
    a.created_by_user_displayname, a.created_by_user_email,
    a.created_by_user_sub, a.group_uuid
FROM antibodies a
JOIN vendors v ON a.vendor_id = v.id
'''

def test_post_with_no_body_should_return_400(client, headers):
    response = client.post('/antibodies', headers=headers)
    assert response.status == '400 BAD REQUEST'

class AntibodyTesting:
    # pylint: disable=no-self-use,unused-argument
    @pytest.fixture
    def ant_query(self):
        return base_antibody_query() + 'WHERE a.id = %s'

    @pytest.fixture
    def last_antibody_data(self, ant_query, cursor, last_antibody_id):
        cursor.execute(ant_query, (last_antibody_id,))
        return cursor.fetchone()

    @pytest.fixture
    def last_antibody_id(self, cursor):
        cursor.execute('SELECT id FROM antibodies ORDER BY id DESC LIMIT 1')
        try:
            return cursor.fetchone()[0]
        except TypeError:
            return None

    @pytest.fixture
    def last_vendor_data(self, cursor):
        cursor.execute('SELECT name FROM vendors ORDER BY id DESC LIMIT 1')
        try:
            return cursor.fetchone()[0]
        except TypeError:
            return None

    @pytest.fixture
    def initial_antibodies_count(self, cursor):
        return self.get_antibodies_count(cursor)

    @pytest.fixture
    def final_antibodies_count(self, cursor):
        return self.get_antibodies_count(cursor)

    @pytest.fixture
    def initial_vendor_count(self, cursor):
        return self.get_vendors_count(cursor)

    @pytest.fixture
    def final_vendor_count(self, cursor):
        return self.get_vendors_count(cursor)

    @classmethod
    def get_antibodies_count(cls, cursor):
        cursor.execute('SELECT COUNT(*) AS count FROM antibodies')
        return cursor.fetchone()[0]

    @classmethod
    def get_vendors_count(cls, cursor):
        cursor.execute('SELECT COUNT(*) AS count FROM vendors')
        return cursor.fetchone()[0]

class TestGetAntibodies:
    # pylint: disable=no-self-use
    @pytest.fixture(scope='class')
    def response(self, client, headers, antibody_data):
        client.post('/antibodies', data=json.dumps(antibody_data), headers=headers)
        return client.get('/antibodies', headers=headers)

    def test_should_return_a_200_response(self, response):
        assert response.status == '200 OK'

    def test_all_antibody_fields_are_retrieved_correctly(
        self, response, antibody_data
    ):
        assert antibody_data['antibody'] == json.loads(response.data)['antibodies'][0]

class TestPostCSVFile(AntibodyTesting):
    # pylint: disable=no-self-use, unused-argument
    @classmethod
    def last_query(cls):
        return base_antibody_query() + ' ORDER BY a.id DESC LIMIT 1'

    @classmethod
    def last_antibody(cls, cursor):
        cursor.execute(cls.last_query())
        return cursor.fetchone()

    @pytest.fixture
    def response(self, client, headers, request_data):
        yield client.post(
            '/antibodies/import',
            content_type='multipart/form-data',
            data=request_data,
            headers=headers
        )

    @pytest.fixture
    def response_to_empty_request(self, client, headers):
        return client.post('/antibodies/import', headers=headers)

    @pytest.fixture
    def response_to_request_without_filename(self, client, headers, csv_file):
        return client.post(
            '/antibodies/import',
            content_type='multipart/form-data',
            data={'file': (io.BytesIO(csv_file), '')},
            headers=headers
        )

    @pytest.fixture
    def response_to_request_with_wrong_extension(self, client, headers, csv_file):
        return client.post(
            '/antibodies/import',
            content_type='multipart/form-data',
            data={'file': (io.BytesIO(csv_file), 'data.zip')},
            headers=headers
        )

    @pytest.fixture
    def response_to_request_with_weird_csv_file(self, client, headers, weird_csv_file):
        return client.post(
            '/antibodies/import',
            content_type='multipart/form-data',
            data={'file': (io.BytesIO(weird_csv_file), 'antibodies.csv')},
            headers=headers
        )

    @pytest.fixture
    def request_data(self, csv_file):
        return {'file': (io.BytesIO(csv_file), 'antibodies.csv')}

    @pytest.fixture
    def csv_file(self, antibody_data_multiple):
        fields = ','.join(antibody_data_multiple['antibody'][0].keys())
        values = ''
        for antibody in antibody_data_multiple['antibody']:
            values += ','.join(str(v) for v in antibody.values()) + '\n'
        return bytes(fields + '\n' + values, 'utf-8')

    @pytest.fixture
    def weird_csv_file(self):
        return bytes('a,b,c,d\n1,2,1,1\n1,2,1,4\n', 'utf-8')

    def test_post_csv_file_should_save_antibodies_correctly(
        self, response, antibody_data_multiple, cursor
    ):
        assert tuple(
            antibody_data_multiple['antibody'][-1].values()
        ) == self.last_antibody(cursor)

    def test_post_csv_file_should_return_406_if_weird_csv_file_was_sent(
        self, response_to_request_with_weird_csv_file
    ):
        assert response_to_request_with_weird_csv_file.status == '406 NOT ACCEPTABLE'

    def test_post_csv_file_should_return_error_message_if_weird_csv_file_was_sent(
        self, response_to_request_with_weird_csv_file
    ):
        assert json.loads(response_to_request_with_weird_csv_file.data) == {
            'message': 'CSV fields are wrong'
        }

    def test_post_csv_file_should_return_406_if_no_filename_was_sent(
        self, response_to_request_without_filename
    ):
        assert response_to_request_without_filename.status == '406 NOT ACCEPTABLE'

    def test_post_csv_file_should_return_error_message_if_no_filename_was_sent(
        self, response_to_request_without_filename
    ):
        assert json.loads(response_to_request_without_filename.data) == {
            'message': 'Filename missing'
        }

    def test_post_csv_file_should_return_406_if_no_file_was_sent(
        self, response_to_empty_request
    ):
        assert response_to_empty_request.status == '406 NOT ACCEPTABLE'

    def test_post_csv_file_should_return_error_message_if_no_file_was_sent(
        self, response_to_empty_request
    ):
        assert json.loads(response_to_empty_request.data) == {
            'message': 'CSV file missing'
        }

    def test_post_csv_file_should_return_406_if_file_has_not_csv_extension(
        self, response_to_request_with_wrong_extension
    ):
        assert response_to_request_with_wrong_extension.status == '406 NOT ACCEPTABLE'

    def test_post_csv_file_should_return_error_message_if_file_has_not_csv_extension(
        self, response_to_request_with_wrong_extension
    ):
        assert json.loads(response_to_request_with_wrong_extension.data) == {
            'message': 'Filetype forbidden'
        }

    def test_post_csv_file_should_return_a_204_response(self, response):
        assert response.status == '204 NO CONTENT'

    def test_antibody_count_in_database_should_increase(
        self, initial_antibodies_count, response, final_antibodies_count,
        antibody_data_multiple
    ):
        assert (
            final_antibodies_count
        ) == len(antibody_data_multiple['antibody'])

class TestPostEmptyJSONBody:
    # pylint: disable=no-self-use
    @pytest.fixture(scope='class')
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
    @pytest.fixture(scope='class')
    def removed_field(self, antibody_incomplete_data):
        return antibody_incomplete_data[1]

    @pytest.fixture(scope='class')
    def incomplete_data(self, antibody_incomplete_data):
        return antibody_incomplete_data[0]

    @pytest.fixture(scope='class')
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

class TestPostWithCompleteJSONBody(AntibodyTesting):
    # pylint: disable=no-self-use, unused-argument
    @pytest.fixture
    def add_vendor(self, cursor, antibody_data):
        cursor.execute(
            'INSERT INTO vendors (name) VALUES (%s)',
            (antibody_data['antibody']['vendor'],)
        )

    @pytest.fixture
    def add_vendor_uppercase(self, cursor, antibody_data):
        cursor.execute(
            'INSERT INTO vendors (name) VALUES (%s)',
            (antibody_data['antibody']['vendor'].upper(),)
        )

    @pytest.fixture
    def response(self, client, antibody_data, headers, initial_antibodies_count):
        return client.post('/antibodies', data=json.dumps(antibody_data), headers=headers)

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

    def test_api_should_create_a_new_vendor_if_it_does_not_exist_already(
        self, initial_vendor_count, response, final_vendor_count
    ):
        assert (initial_vendor_count + 1) == final_vendor_count

    def test_api_should_save_new_vendor_correctly(
        self, response, antibody_data, last_vendor_data
    ):
        assert antibody_data['antibody']['vendor'] == last_vendor_data

    def test_api_should_not_create_vendor_if_it_exists_already(
        self, add_vendor, initial_vendor_count, response, final_vendor_count
    ):
        assert initial_vendor_count == final_vendor_count

    def test_api_should_identify_vendor_regardless_of_case(
        self, add_vendor_uppercase, initial_vendor_count, response, final_vendor_count
    ):
        assert initial_vendor_count == final_vendor_count
