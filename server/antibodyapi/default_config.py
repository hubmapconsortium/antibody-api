# pylint: disable=too-few-public-methods
from datetime import timedelta


class DefaultConfig:
    # This should be updated when app.conf is updated:
    # Test runs will only see this config and not app.conf.
    #
    # Tests should not make API calls...
    # but they may expect certain keys to be present.

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_COOKIE_SAMESITE = 'Lax'

    PORTAL_INDEX_PATH = '/portal/search'
    CCF_INDEX_PATH = '/entities/search'

    DATABASE_HOST = 'db'
    DATABASE_NAME = 'antibodydb_test'
    DATABASE_USER = 'postgres'
    DATABASE_PASSWORD = 'password'

    # Everything else should be overridden in app.conf:

    ENTITY_API_BASE = 'should-be-overridden'
    SEARCH_API_BASE = 'should-be-overridden'

    GROUP_ID = 'should-be-overridden'

    # TODO: ELASTICSEARCH_ENDPOINT is not used but ELASTICSEARCH_SERVER is used. This is confusing and should be resolved as only one should be used.
#    ELASTICSEARCH_ENDPOINT = 'should-be-overridden'
    ASSETS_ENDPOINT = 'should-be-overridden'
    CELLS_API_ENDPOINT = 'should-be-overridden'

    SECRET_KEY = 'should-be-overridden'
    APP_CLIENT_ID = 'should-be-overridden'
    APP_CLIENT_SECRET = 'should-be-overridden'

    UUID_API_URL = 'http://uuidmock:1080'
    INGEST_API_URL = 'http://uuidmock:1080'
    # This is the name of the container in the docker-compose file.
    ELASTICSEARCH_SERVER = 'http://elasticsearch'
    ANTIBODY_ELASTICSEARCH_INDEX = 'hm_antibodies'
    QUERY_ELASTICSEARCH_DIRECTLY = False
