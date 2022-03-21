#!/bin/bash
set -e
set -u

POSTGRES_USER=postgres
POSTGRES_DB=antibodydb_test

echo "Dropping and Creating test database..."
psql -v ON_ERROR_STOP=1 -h localhost -U $POSTGRES_USER -a <<-EOSQL
  DROP DATABASE IF EXISTS ${POSTGRES_DB};
  CREATE DATABASE ${POSTGRES_DB};
EOSQL

echo "Creating tables in test database..."
#psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -f /docker-entrypoint-initdb.d/create_tables.sql ${POSTGRES_DB}_test
psql -v ON_ERROR_STOP=1 -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -a -f ./development/postgresql_init_scripts/create_tables.sql
