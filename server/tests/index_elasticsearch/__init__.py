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
    def response(
        self, client, antibody_data, headers, create_uuid_expectation, mocker
    ):
        with client.session_transaction() as sess:
            sess['is_authenticated'] = True
            sess['tokens'] = {'nexus.api.globus.org': {'access_token': 'woot'}}
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

    def test_antibody_gets_indexed_in_elasticsearch(self, response):
        response.assert_called()
