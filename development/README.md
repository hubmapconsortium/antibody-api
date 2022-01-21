# Development

These files are only used in a development scenario.
They are used for the PostgreSQL container to initialize the database.
They won't run if the database already exists.

The work automatically though the docker-compose file for development.

In a non-development scenario it is assumed that the database has already been defined.
In a deployment scenario you only need to run 'create_tables.sql' to create the database for the first time.
