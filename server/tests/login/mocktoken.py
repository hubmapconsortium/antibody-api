class MockToken:
    # pylint: disable=no-self-use, too-few-public-methods
    def __init__(self):
        pass
    def get_resource_server(self):
        return 'WOOT WOOT'
    by_resource_server=property(get_resource_server)
