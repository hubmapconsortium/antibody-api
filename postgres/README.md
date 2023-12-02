# Development

These files are only used in a development scenario.
They are used for the PostgreSQL container to initialize the database.
They won't run if the database already exists.

They may work automatically though the docker-compose file for development. If not, use the following.
```bash
$ psql -h localhost -U postgres -d antibodydb -a -f ./development/postgresql_init_scripts/create_tables.sql 
```
The database information should be found in the './instance/app.conf' file which overwrites the './server/antibodyapi/default_config.py'.
```bash
$ psql -h localhost -U DATABASE_USER -d DATABASE_NAME -a -f ./development/postgresql_init_scripts/create_tables.sql 
```
For the password, use the DATABASE_PASSWORD.

In a non-development scenario it is assumed that the database has already been defined.
In a deployment scenario you only need to run 'create_tables.sql' to create the database for the first time.
