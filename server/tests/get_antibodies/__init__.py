import json
import pytest
from antibody_testing import AntibodyTesting

class TestGetAntibodies(AntibodyTesting):
    # pylint: disable=no-self-use, unused-argument
    @pytest.fixture(scope='class')
    def create_uuid_expectation(self, flask_app, headers, antibody_data):
        self.create_expectation(flask_app, headers, antibody_data['antibody'], 0)

    @pytest.fixture(scope='class')
    def response(self, client, headers, antibody_data, create_uuid_expectation):
        with client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['tokens'] = { 'nexus.api.globus.org' : { 'access_token': 'woot' } }
            sess['name'] = 'Name'
            sess['email'] = 'name@example.com'
            sess['sub'] = '1234567890'
        client.post('/antibodies', data=json.dumps(antibody_data), headers=headers)
        return client.get('/antibodies', headers=headers)

    def test_should_return_a_200_response(self, response):
        """GET /antibodies should return 200 OK"""
        assert response.status == '200 OK'

    def test_all_antibody_fields_are_retrieved_correctly(
        self, response, antibody_data
    ):
        """GET /antibodies should return expected fields"""
        received_antibody = json.loads(response.data)['antibodies'][-1]
        expected_fields = (
            'antibody_uuid',
            'created_by_user_displayname',
            'created_by_user_email',
            'created_by_user_sub',
            'group_uuid'
        )
        expected_data = { k: v for k, v in received_antibody.items() if k not in expected_fields }
        sent_data = { k: v for k, v in antibody_data['antibody'].items() if k[0] != '_' }
        print(expected_data)
        assert sent_data == expected_data
