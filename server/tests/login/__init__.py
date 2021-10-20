from flask import session, url_for
import globus_sdk
import pytest
from .mockclient import MockClient
from .mocktoken import MockToken

class TestLogin:
    # pylint: disable=no-self-use, no-member, unused-argument
    def test_should_return_redirection_to_auth_uri(self, client, mocker):
        mocker.patch('globus_sdk.ConfidentialAppAuthClient', new=MockClient)
        response = client.get('/login')
        assert response.status == '302 FOUND'
        assert response.location == MockClient().oauth2_get_authorize_url()

    def test_should_use_correct_client_id_and_secret(self, client, mocker):
        mocker.patch('globus_sdk.ConfidentialAppAuthClient')
        client.get('/login')
        globus_sdk.ConfidentialAppAuthClient.assert_called_once_with(
            'should-be-overridden', 'should-be-overridden'
        )

    def test_should_call_oauth2_start_flow(self, client, mocker):
        mock = mocker.patch.object(MockClient,'oauth2_start_flow')
        mocker.patch('globus_sdk.ConfidentialAppAuthClient', new=MockClient)
        client.get('/login')
        mock.assert_called_once_with(url_for('login.login', _external=True))

    @pytest.fixture
    def login_with_code(self, client, mocker):
        mocker.patch('globus_sdk.ConfidentialAppAuthClient', new=MockClient)
        mocker.patch('globus_sdk.AuthClient', new=MockClient)
        mocker.patch('globus_sdk.AccessTokenAuthorizer', new=MockClient)
        return client.get('/login', query_string={'code': 123})

    def test_request_with_code_should_return_redirection_to_index(self, login_with_code):
        assert login_with_code.status == '302 FOUND'
        assert login_with_code.location == 'http://localhost%s' % (url_for('hubmap.hubmap'),)

    def test_request_with_code_should_save_tokens_in_session(self, login_with_code):
        assert session['tokens'] == MockToken().get_resource_server()
        assert session['is_authenticated'] is True
