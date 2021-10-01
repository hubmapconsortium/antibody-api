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

    GROUP_ID = 'should-be-overridden'

    ELASTICSEARCH_ENDPOINT = 'should-be-overridden'
    ASSETS_ENDPOINT = 'should-be-overridden'

    SECRET_KEY = 'should-be-overridden'
    APP_CLIENT_ID = 'should-be-overridden'
    APP_CLIENT_SECRET = 'should-be-overridden'

    UUID_API_URL = 'http://uuidmock:1080'
    INGEST_API_URL = 'http://ingestmock:1080'
