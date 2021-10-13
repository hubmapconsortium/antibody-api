import json
import pytest

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

    def test_post_with_incomplete_json_body_should_return_400(
            self, response
        ):
        """POST /antibodies with incomplete JSON body
         should return 400 BAD REQUEST"""
        assert response.status == '400 BAD REQUEST'

    def test_post_with_incomplete_json_body_should_return_error_message(
            self, response, removed_field
        ):
        """POST /antibodies with incomplete JSON body
        should return an error message about it"""
        assert json.loads(response.data) == {
            'message': 'Antibody data incomplete: missing %s parameter' % removed_field
        }
