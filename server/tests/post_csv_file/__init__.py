import io
import json
import pytest
from antibody_testing import AntibodyTesting
from base_antibody_query import base_antibody_query

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
    def response_to_two_csv_files(self, client, headers, request_data_two_csv_files):
        yield client.post(
            '/antibodies/import',
            content_type='multipart/form-data',
            data=request_data_two_csv_files,
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

    def test_post_csv_file_should_save_antibodies_correctly(
        self, response, antibody_data_multiple, cursor
    ):
        """Posting a CSV file should save antibodies correctly"""
        assert tuple(
            antibody_data_multiple['antibody'][-1].values()
        ) == self.last_antibody(cursor)

    def test_post_csv_file_should_return_a_204_response(self, response):
        """Sending a CSV file should return 204 NO CONTENT if all goes well"""
        assert response.status == '204 NO CONTENT'

    def test_antibody_count_in_database_should_increase(
        self, initial_antibodies_count, response, final_antibodies_count,
        antibody_data_multiple
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
