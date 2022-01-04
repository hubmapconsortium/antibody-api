import io
import json
import pytest
from antibody_testing import AntibodyTesting
from .mock_es import MockES

class TestElasticsearchIndexing(AntibodyTesting):
    # pylint: disable=no-self-use, unused-argument, too-many-arguments
    @pytest.fixture
    def create_uuid_expectation(self, flask_app, headers, antibody_data):
        self.create_expectation(flask_app, headers, antibody_data['antibody'], 0)

    @pytest.fixture
    def response_single_json_body(
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
        mock = mocker.patch.object(MockES, 'index')
        mocker.patch('elasticsearch.Elasticsearch', new=MockES)
        client.post('/antibodies', data=json.dumps(data_to_send), headers=headers)
        return mock

    def test_antibody_gets_indexed_in_elasticsearch(self, response_single_json_body):
        response_single_json_body.assert_called()

    @pytest.fixture(scope='class')
    def response_csv_file(
        self, client, headers, request_data, create_group_expectations,
        create_expectations, class_mocker
    ):
        with client.session_transaction() as sess:
            sess['is_authenticated'] = True
            sess['groups_access_token'] = 'woot'
            sess['name'] = 'Name'
            sess['email'] = 'name@example.com'
            sess['sub'] = '1234567890'
        mock = class_mocker.patch.object(MockES, 'index')
        class_mocker.patch('elasticsearch.Elasticsearch', new=MockES)
        client.post(
            '/antibodies/import',
            content_type='multipart/form-data',
            data=request_data,
            headers=headers
        )
        return mock

    @pytest.fixture(scope='class')
    def create_expectations(self, flask_app, headers, antibody_data_multiple):
        for idx, antibody in enumerate(antibody_data_multiple['antibody']):
            self.create_expectation(flask_app, headers, antibody, idx)

    @pytest.fixture(scope='class')
    def create_group_expectations(
        self, flask_app, group_id
    ):
        self.create_group_id_expectation(flask_app, group_id)

    @pytest.fixture(scope='class')
    def request_data(self, csv_file):
        return {'file': (io.BytesIO(csv_file), 'antibodies.csv')}

    @pytest.fixture(scope='class')
    def csv_file(self, antibody_data_multiple):
        fields = ','.join(antibody_data_multiple['antibody'][0].keys())
        values = ''
        for antibody in antibody_data_multiple['antibody']:
            values += ','.join(str(v) for v in antibody.values()) + '\n'
        return bytes(fields + '\n' + values, 'utf-8')

    def test_antibodies_get_indexed_in_elasticsearch(
        self, antibody_data_multiple, response_csv_file
    ):
        assert response_csv_file.call_count == len(antibody_data_multiple['antibody'])
