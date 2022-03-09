#!/bin/sh

DATABASE_HOST='localhost'
DATABASE_NAME='antibodydb'
DATABASE_USER='postgres'
DATABASE_PASSWORD='password'

ANTIBODY_URL='localhost:5000'

if [[ `which psql > /dev/null 2>&1 ; echo $?` -ne 0 ]] ; then
  brew install postgresql
fi

export PGPASSWORD=$DATABASE_PASSWORD
psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -c "DROP TABLE IF EXISTS antibodies, vendors"
psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -f ../development/postgresql_init_scripts/create_tables.sql

# Rebuild the index
curl -X PUT --header 'Content-Type: application/json' "${ANTIBODY_URL}/restore_elasticsearch"
