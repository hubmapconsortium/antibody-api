import io
import json
import pytest
import requests
from antibody_testing import AntibodyTesting
from base_antibody_query import base_antibody_query, base_antibody_query_without_antibody_uuid

class TestPostCSVFile(AntibodyTesting):
    # pylint: disable=no-self-use, unused-argument
    @classmethod
    def last_query(cls):
        return base_antibody_query_without_antibody_uuid() + ' ORDER BY a.id DESC LIMIT 1'

    @classmethod
    def last_antibody(cls, cursor):
        cursor.execute(cls.last_query())
        return cursor.fetchone()

    @classmethod
    def antibody_uuid(cls, cursor, antibody_name):
        cursor.execute(
            base_antibody_query() + ' WHERE a.antibody_name = %(antibody_name)s',
            { 'antibody_name': antibody_name }
        )
        return cursor.fetchone()[0]

    @classmethod
    def get_antibody_file_name(cls, cursor, uuid):
        cursor.execute(
            'SELECT avr_filename FROM antibodies WHERE antibody_uuid = %(antibody_uuid)s',
            { 'antibody_uuid': uuid }
        )
        try:
            avr_filename = cursor.fetchone()[0]
        except: # pylint: disable=bare-except
            avr_filename = None
        return avr_filename

    @classmethod
    def get_antibody_file_uuid(cls, cursor, uuid):
        cursor.execute(
            'SELECT avr_uuid FROM antibodies WHERE antibody_uuid = %(antibody_uuid)s',
            { 'antibody_uuid': uuid }
        )
        return cursor.fetchone()[0]

    @classmethod
    def create_file_expectation(cls, flask_app, headers, antibody, idx):
        requests.put(
            '%s/mockserver/expectation' % (flask_app.config['INGEST_API_URL'],),
            json={
                'httpRequest': {
                    'method': 'POST',
                    'path': '/file-upload',
                    'headers': {
                        'authorization': [ headers['authorization'] ],
                        'Content-Type': [ 'multipart/form-data' ]
                    }
                },
                'httpResponse': {
                    'body': {
                        'contentType': 'application/json',
                        'json': json.dumps({'temp_file_id': 'temp_file_id'})
                    }
                },
                'times': {
                    'remainingTimes': 1,
                    'unlimited': False
                },
                'priority': 1000-idx
            }
        )
        requests.put(
            '%s/mockserver/expectation' % (flask_app.config['INGEST_API_URL'],),
            json={
                'httpRequest': {
                    'method': 'POST',
                    'path': '/file-commit',
                    'headers': {
                        'authorization': [ headers['authorization'] ],
                        'Content-Type': [ 'application/json' ]
                    },
                    'body': {
                        'entity_uuid': antibody['_antibody_uuid'],
                        'temp_file_id': 'temp_file_id',
                        'user_token': headers['authorization'].split()[-1]
                    }
                },
                'httpResponse': {
                    'body': {
                        'contentType': 'application/json',
                        'json': json.dumps([{
                            'file_uuid': antibody['_pdf_uuid'],
                            'filename': antibody['avr_filename']
                        }])
                    }
                },
                'times': {
                    'remainingTimes': 1,
                    'unlimited': False
                },
                'priority': 1000-idx
            }
        )

    @classmethod
    def create_pdf(cls):
        return bytes('a,b,c,d\n1,2,1,1\n1,2,1,4\n', 'utf-8')

    @pytest.fixture
    def create_expectations(self, flask_app, headers, antibody_data_multiple):
        for idx, antibody in enumerate(antibody_data_multiple['antibody']):
            self.create_expectation(flask_app, headers, antibody, idx)

    @pytest.fixture
    def create_expectations_for_several_csv_files(
        self, flask_app, headers,
        antibody_data_multiple_once, antibody_data_multiple_twice
    ):
        for idx, antibody in enumerate(
            antibody_data_multiple_once['antibody'] +
            antibody_data_multiple_twice['antibody']
        ):
            self.create_expectation(flask_app, headers, antibody, idx)

    @pytest.fixture
    def create_expectations_for_several_pdf_files(
        self, flask_app, headers, antibody_data_multiple_with_pdfs
    ):
        for idx, antibody in enumerate(antibody_data_multiple_with_pdfs['antibody']):
            self.create_expectation(flask_app, headers, antibody, idx)
            self.create_file_expectation(flask_app, headers, antibody, idx)

    @pytest.fixture
    def response(self, client, headers, request_data, create_expectations):
        yield client.post(
            '/antibodies/import',
            content_type='multipart/form-data',
            data=request_data,
            headers=headers
        )

    @pytest.fixture
    def response_to_two_csv_files(
        self, client, headers, request_data_two_csv_files,
        create_expectations_for_several_csv_files
    ):
        yield client.post(
            '/antibodies/import',
            content_type='multipart/form-data',
            data=request_data_two_csv_files,
            headers=headers
        )

    @pytest.fixture
    def response_to_csv_and_pdfs( # pylint: disable=too-many-arguments
        self, client, headers, request_data_with_pdfs,
        create_expectations_for_several_pdf_files
    ):
        yield client.post(
            '/antibodies/import',
            content_type='multipart/form-data',
            data=request_data_with_pdfs,
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
    def request_data_two_csv_files(self, csv_file_once, csv_file_twice):
        return {
            'file': [
                (io.BytesIO(csv_file_once), 'antibodies.csv'),
                (io.BytesIO(csv_file_twice), 'more-antibodies.csv')
            ]
        }

    @pytest.fixture
    def request_data_with_pdfs(
        self, antibody_data_multiple_with_pdfs, csv_file_with_random_avr_filenames
    ):
        data = {'file': (io.BytesIO(csv_file_with_random_avr_filenames), 'antibodies.csv')}
        pdf_files = []
        for antibody in antibody_data_multiple_with_pdfs['antibody']:
            pdf_files.append((io.BytesIO(self.create_pdf()), antibody['avr_filename']))
        data['pdf'] = pdf_files
        return data

    @pytest.fixture
    def csv_file_with_random_avr_filenames(self, antibody_data_multiple_with_pdfs):
        relevant_keys = []
        for k in antibody_data_multiple_with_pdfs['antibody'][0].keys():
            if k[0] != '_':
                relevant_keys.append(k)
        fields = ','.join(relevant_keys)
        values = ''
        for antibody in antibody_data_multiple_with_pdfs['antibody']:
            relevant_values = []
            for k, val in antibody.items():
                if k[0] != '_':
                    relevant_values.append(val)
            values += ','.join(str(v) for v in relevant_values) + '\n'
        return bytes(fields + '\n' + values, 'utf-8')

    @pytest.fixture
    def csv_file(self, antibody_data_multiple):
        fields = ','.join(antibody_data_multiple['antibody'][0].keys())
        values = ''
        for antibody in antibody_data_multiple['antibody']:
            values += ','.join(str(v) for v in antibody.values()) + '\n'
        return bytes(fields + '\n' + values, 'utf-8')

    @pytest.fixture
    def csv_file_once(self, antibody_data_multiple_once):
        fields = ','.join(antibody_data_multiple_once['antibody'][0].keys())
        values = ''
        for antibody in antibody_data_multiple_once['antibody']:
            values += ','.join(str(v) for v in antibody.values()) + '\n'
        return bytes(fields + '\n' + values, 'utf-8')

    @pytest.fixture
    def csv_file_twice(self, antibody_data_multiple_twice):
        fields = ','.join(antibody_data_multiple_twice['antibody'][0].keys())
        values = ''
        for antibody in antibody_data_multiple_twice['antibody']:
            values += ','.join(str(v) for v in antibody.values()) + '\n'
        return bytes(fields + '\n' + values, 'utf-8')

    @pytest.fixture
    def weird_csv_file(self):
        return bytes('a,b,c,d\n1,2,1,1\n1,2,1,4\n', 'utf-8')

    def test_post_csv_file_with_pdf_should_save_those_correctly(
        self, response_to_csv_and_pdfs, antibody_data_multiple_with_pdfs, cursor
    ):
        """ Posting PDF files should get them saved"""
        for antibody in antibody_data_multiple_with_pdfs['antibody']:
            assert antibody['avr_filename'] == self.get_antibody_file_name(
                cursor, antibody['_antibody_uuid']
            )
            assert antibody['_pdf_uuid'] == self.get_antibody_file_uuid(
                cursor, antibody['_antibody_uuid']
            )

    def test_post_csv_file_should_save_antibodies_correctly(
        self, response, antibody_data_multiple, cursor
    ):
        """Posting a CSV file should save antibodies correctly"""
        sent_data = {
            k: v for k, v in antibody_data_multiple['antibody'][-1].items() if k[0] != '_'
        }
        assert tuple(
            sent_data.values()
        ) == self.last_antibody(cursor)

    def test_post_csv_file_should_return_a_204_response(self, response):
        """Sending a CSV file should return 204 NO CONTENT if all goes well"""
        assert response.status == '204 NO CONTENT'

    def test_antibody_count_in_database_should_increase(
        self, initial_antibodies_count, response,
        final_antibodies_count, antibody_data_multiple
    ):
        """When sending a CSV file successfully, antibody count should increase"""
        assert (
            final_antibodies_count
        ) >= len(antibody_data_multiple['antibody'])

    def test_antibody_count_in_database_should_increase_when_sending_several_csvs(
        self, initial_antibodies_count, response_to_two_csv_files,
        final_antibodies_count, antibody_data_multiple_once,
        antibody_data_multiple_twice
    ): # pylint: disable=too-many-arguments
        """When sending two CSV files successfully, antibody count should increase"""
        assert (
            final_antibodies_count
        ) >= (
            len(antibody_data_multiple_once['antibody']) +
            len(antibody_data_multiple_twice['antibody'])
        )

    def test_post_csv_file_should_return_406_if_weird_csv_file_was_sent(
        self, response_to_request_with_weird_csv_file
    ):
        """Posting a weird CSV file should return 406 NOT ACCEPTABLE"""
        assert response_to_request_with_weird_csv_file.status == '406 NOT ACCEPTABLE'

    def test_post_csv_file_should_return_error_message_if_weird_csv_file_was_sent(
        self, response_to_request_with_weird_csv_file
    ):
        """Posting a weird CSV file should return a message about it"""
        assert json.loads(response_to_request_with_weird_csv_file.data) == {
            'message': 'CSV fields are wrong'
        }

    def test_post_csv_file_should_return_406_if_no_filename_was_sent(
        self, response_to_request_without_filename
    ):
        """Posting a CSV file with no filename should return 406 NOT ACCEPTABLE"""
        assert response_to_request_without_filename.status == '406 NOT ACCEPTABLE'

    def test_post_csv_file_should_return_error_message_if_no_filename_was_sent(
        self, response_to_request_without_filename
    ):
        """Posting a CSV file with no filename should return a message about it"""
        assert json.loads(response_to_request_without_filename.data) == {
            'message': 'Filename missing'
        }

    def test_post_csv_file_should_return_406_if_no_file_was_sent(
        self, response_to_empty_request
    ):
        """Return 406 NOT ACCEPTABLE if no CSV file was sent at all"""
        assert response_to_empty_request.status == '406 NOT ACCEPTABLE'

    def test_post_csv_file_should_return_error_message_if_no_file_was_sent(
        self, response_to_empty_request
    ):
        """Return an error message if no CSV file was sent at all"""
        assert json.loads(response_to_empty_request.data) == {
            'message': 'CSV file missing'
        }

    def test_post_csv_file_should_return_406_if_file_has_not_csv_extension(
        self, response_to_request_with_wrong_extension
    ):
        """Sending a file with an extension other than CSV should return 406 NOT ACCEPTABLE"""
        assert response_to_request_with_wrong_extension.status == '406 NOT ACCEPTABLE'

    def test_post_csv_file_should_return_error_message_if_file_has_not_csv_extension(
        self, response_to_request_with_wrong_extension
    ):
        """Sending a file with an extension other than CSV should return an error about it"""
        assert json.loads(response_to_request_with_wrong_extension.data) == {
            'message': 'Filetype forbidden'
        }
