class MockToken:
    # pylint: disable=no-self-use, too-few-public-methods
    def __init__(self):
        pass
    def get_resource_server(self):
        return {
            'whatever': {'access_token': 'WOOTWOOT'},
            'auth.globus.org': {'access_token': 'WOOTWOOT'},
            'groups.api.globus.org': {'access_token': 'WOOTWOOT'}
        }
    by_resource_server=property(get_resource_server)
