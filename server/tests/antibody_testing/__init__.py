import pytest
from base_antibody_query import base_antibody_query_without_antibody_uuid

class AntibodyTesting:
    # pylint: disable=no-self-use,unused-argument
    @pytest.fixture
    def ant_query(self):
        return base_antibody_query_without_antibody_uuid() + 'WHERE a.id = %s'

    @pytest.fixture
    def last_antibody_data(self, ant_query, cursor, last_antibody_id):
        cursor.execute(ant_query, (last_antibody_id,))
        return cursor.fetchone()

    @pytest.fixture
    def last_antibody_id(self, cursor):
        cursor.execute('SELECT id FROM antibodies ORDER BY id DESC LIMIT 1')
        try:
            return cursor.fetchone()[0]
        except TypeError:
            return None

    @pytest.fixture
    def last_vendor_data(self, cursor):
        cursor.execute('SELECT name FROM vendors ORDER BY id DESC LIMIT 1')
        try:
            return cursor.fetchone()[0]
        except TypeError:
            return None

    @pytest.fixture
    def initial_antibodies_count(self, cursor):
        return self.get_antibodies_count(cursor)

    @pytest.fixture
    def final_antibodies_count(self, cursor):
        return self.get_antibodies_count(cursor)

    @pytest.fixture
    def initial_vendor_count(self, cursor):
        return self.get_vendors_count(cursor)

    @pytest.fixture
    def final_vendor_count(self, cursor):
        return self.get_vendors_count(cursor)

    @classmethod
    def get_antibodies_count(cls, cursor):
        cursor.execute('SELECT COUNT(*) AS count FROM antibodies')
        return cursor.fetchone()[0]

    @classmethod
    def get_vendors_count(cls, cursor):
        cursor.execute('SELECT COUNT(*) AS count FROM vendors')
        return cursor.fetchone()[0]
