import json
import pytest

class TestGetAntibodies:
    # pylint: disable=no-self-use
    @pytest.fixture(scope='class')
    def response(self, client, headers, antibody_data):
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
        del received_antibody['antibody_uuid']
        assert antibody_data['antibody'] == received_antibody
