from .mocktoken import MockToken

class MockClient:
    # pylint: disable=no-self-use
    def __init__(self, *_):
        pass
    def oauth2_exchange_code_for_tokens(self, *_):
        return MockToken()
    def oauth2_get_authorize_url(self):
        return 'http://http.cat'
    def oauth2_start_flow(self, *_):
        pass
