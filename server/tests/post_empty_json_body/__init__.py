import json
import pytest

class TestPostEmptyJSONBody:
    # pylint: disable=no-self-use
    @pytest.fixture(scope='class')
    def response(self, client, headers):
        return client.post(
            '/antibodies', data=json.dumps({}), headers=headers
        )

    def test_post_with_empty_json_body_should_return_406(self, response):
        """POST /antibodies with an empty JSON body should return 406 NOT ACCEPTABLE"""
        assert response.status == '406 NOT ACCEPTABLE'

    def test_post_with_empty_json_should_return_error_message(self, response):
        """POST /antibodies with an empty JSON body should return an error about it"""
        assert json.loads(response.data) == {
            'message': 'Antibody missing'
        }
