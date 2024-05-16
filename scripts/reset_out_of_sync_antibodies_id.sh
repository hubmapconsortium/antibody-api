#!/bin/sh

DATABASE_HOST='localhost'
DATABASE_NAME='antibodydb'
DATABASE_USER='postgres'
DATABASE_PASSWORD='password'

if [[ `which psql > /dev/null 2>&1 ; echo $?` -ne 0 ]] ; then
  brew install postgresql
fi

export PGPASSWORD=$DATABASE_PASSWORD

# https://stackoverflow.com/questions/4448340/postgresql-duplicate-key-violates-unique-constraint
echo
echo "If the first value is higher than the second value, your primary key sequence is out of sync."
echo "This can be caused because of data import or copy/paste or data."
echo "If this is the case uncomment the 'exit' below and run again."
psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -c "SELECT MAX(id) FROM antibodies;"
psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -c "SELECT nextval(pg_get_serial_sequence('antibodies', 'id'));"

exit
psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -c "SELECT setval(pg_get_serial_sequence('antibodies', 'id'), (SELECT MAX(id) FROM antibodies) + 1);"
