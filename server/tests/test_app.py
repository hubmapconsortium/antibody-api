# pylint: disable=unused-import
from get_antibodies import TestGetAntibodies
from login import TestLogin
from logout import TestLogout
from post_csv_file import TestPostCSVFile
from post_empty_json_body import TestPostEmptyJSONBody
from post_incomplete_json_body import TestPostIncompleteJSONBody
from post_complete_json_body import TestPostWithCompleteJSONBody

def test_post_with_no_body_should_return_400(client, headers):
    """POST /antibodies with no body should return 400 BAD REQUEST"""
    response = client.post('/antibodies', headers=headers)
    assert response.status == '400 BAD REQUEST'
