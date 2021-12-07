#!/bin/bash
set -e
set -u

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE ${POSTGRES_DB}_test;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -f /docker-entrypoint-initdb.d/create_tables.sql ${POSTGRES_DB}_test
