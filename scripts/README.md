# Scripts

There are scripts for running, testing, linting, and establishing a shell to a Docker container.
There is also a script for building/updating the API generated from the OpenAPI spec.

## OpenAPI Script

This script will create/update the client API from the OpenAPI
specification located at './antibody-api-spec.yml'. The client will be built in the 'hu-bap-antibody-api-client' directory.
```bash
$ ./scripts/build_openapi_client.sh
```

## Verify .csv file upload

This script is used to determine if data in the .csv file is present
in PosgreSQL, ElasticSearch, and Assets. Documentation for running the program is available with the '-h' optional argument.
```bash
$ ./verify_csv_file_was_properly_loaded.py -h
```

## Reloading ElasticSearch from PostgreSQL Database

To delete the current ElaseicSearch index and reload it from the database you can use the following substituting the appropriate ANTIBODY_URL, and TOKEN.
```commandline
$ TOKEN='TheTokenString'; ANTIBODY_URL='https://avr.hubmapconsortium.org'; curl -v -X PUT -H 'Content-Type: application/json' -H "Authorization: Bearer ${TOKEN}" "${ANTIBODY_URL}/restore_elasticsearch"
```
You can get the TOKEN by logging into the [HuBMAP Portal](https://portal.hubmapconsortium.org/),
opening the "Browser Tools", and looking for a request (in the 'Network' section) to one of the other back end services
in the 'Headers' section of that URL and copying the 'Authorization: Bearer TheTokenString'.

## Verify the ElasticSearch matches PostgreSQL

This script is used to determine if all of the data in the PostgreSQL
database is represented in ElasticSearch. It is wise to use it after reloading the ElasticSearch index from the PostgreSQL database.
```bash
$ ./verify_db_in_elasticsearch.py -h
```

## Docker Scripts
These scripts package the docker "magic".  They must be run from the repo root folder.

They all startup Docker containers locally, and so they all need Docker to be running locally.

### Linter

This will run the python linter over the python code and displays the quality.

### Local

This will start the service locally.
The server will be available on [http://localhost:5000](http://localhost:5000).
Before it can be run, the 'instance/app.conf' file must be configured (see ./README.md) as the server makes connections to the services to get a UUID and also to store the .pdf (see ./scrpts/README.md).

While many containers are created by the 'docker-compose.development.yml' file, the local environment depends on services mentioned in the '/instance/app.conf' file (see ./README.md); to get a UUID and also to store the .pdf (see ./scrpts/README.md).
In particular, the UUID_API_URL is used to get the unique identifier for the antibodies, and
the INGEST_API_URL is used to store the .pdf files.

This local script also has a default command that allows you to run any command that you want.
If you add a parameter to the end then it will run that parameter.
By default, it will run 'up -d' which daemonizes it and hides it from your view.
Scenario, './scripts/run_local.sh up' will not daemonize (add the '-d').
You can also bring the server down with  './scripts/run_local.sh down', and 'docker ps' should not show them.

You should note that the database tables (please see /development/postgresql_init_scripts/README.md)
need to be created before the first time that you access the GUI,
and some data must be loaded as well (please see /server/manual_test_files/README.md).
For setup from scratch, please see 'README.md' section 'Deployment Locally'.

To identify the images use 'docker images'.
```bash
$  docker images
REPOSITORY              TAG       IMAGE ID       CREATED        SIZE
antibody-api_web        latest    1812e7e3ab65   2 days ago     956MB
mockserver/mockserver   latest    8d46fe09df91   2 days ago     228MB
postgres                13.3      b2fcd079c1d4   6 months ago   315MB
kibana                  7.4.2     230d3ded1abc   2 years ago    1.1GB
elasticsearch           7.4.2     b1179d41a7b4   2 years ago    855MB
```
To remove the images use 'docker rmi IMAGE ID' for each image.

Then use './scripts/run_local.sh' to rebuild the images and run them.

You may then need to execute 'development/postgresql_init_scripts/create_tables.sql' (see 'development/README.md') to create the tables.

### Terminal

This will create a container for the web service ONLY and will open a terminal session for it.

The use case for this is, if you want to add a library inside a container to get a new requirements file (i.e. with 'pip freese').

### Tests

For information on how to run the tests, please see 'server/tests/README.md'.
