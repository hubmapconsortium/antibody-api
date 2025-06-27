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

    # Everything else should be overridden in app.conf:

    APP_CLIENT_ID = 'should-be-overridden'
    APP_CLIENT_SECRET = 'should-be-overridden'
    
    GROUP_ID = 'should-be-overridden'

    ELASTICSEARCH_SERVER = 'should-be-overridden'
    SEARCH_API_BASE = 'should-be-overridden'
    UUID_API_URL = 'http://uuidmock:1080'
    INGEST_API_URL = 'http://uuidmock:1080'
    ASSETS_URL = 'should-be-overridden'

    ANTIBODY_ELASTICSEARCH_INDEX = 'hm_antibodies'
    QUERY_ELASTICSEARCH_DIRECTLY = False


    DATABASE_HOST = 'db'
    DATABASE_NAME = 'antibodydb_test'
    DATABASE_USER = 'postgres'
    DATABASE_PASSWORD = 'password'
