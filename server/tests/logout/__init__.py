from flask import session, url_for
import globus_sdk
import pytest
from .mockclient import MockClient

class TestLogout:
    # pylint: disable=no-self-use, no-member, unused-argument
    @pytest.fixture
    def logout_response(self, client, mocker):
        mocker.patch('globus_sdk.ConfidentialAppAuthClient', new=MockClient)
        with client.session_transaction() as sess:
            sess['is_authenticated'] = True
        return client.get('/logout')

    def test_should_clear_the_session(self, logout_response):
        assert (not list(session.keys())) is True

    def test_should_return_redirection_to_index(self, logout_response):
        assert logout_response.status == '302 FOUND'
        assert logout_response.location == (
            'https://auth.globus.org/v2/web/logout' +
            '?client={}'.format('should-be-overridden') +
            '&redirect_uri={}'.format(url_for('login.login', _external=True)) +
            '&redirect_name={}'.format('hubmap')
        )

    def test_should_use_correct_client_id_and_secret(self, client, mocker):
        mocker.patch('globus_sdk.ConfidentialAppAuthClient')
        client.get('/logout')
        globus_sdk.ConfidentialAppAuthClient.assert_called_once_with(
            'should-be-overridden', 'should-be-overridden'
        )

    def test_tokens_should_be_revoked(self, client, mocker):
        mock = mocker.patch.object(MockClient,'oauth2_revoke_token')
        mocker.patch('globus_sdk.ConfidentialAppAuthClient', new=MockClient)
        with client.session_transaction() as sess:
            sess['tokens'] = {'whatever': {'access_token': 'WOOTWOOT'}}
        client.get('/logout')
        mock.assert_called_once_with('WOOTWOOT')
