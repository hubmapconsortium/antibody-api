# antibody-api

## Development environment

The development environment has the following services:

* web: the API that listens on port 5000
* kibana: the ES tool that listens on port 5601
* mockserver: used during testing to mock calls to HuBMAP APIs
* elasticsearch: the ES server
* db: the Postgres server

The folder `development_environment/postgresql_init_scripts` contains two files that will be executed in alphabetical order upon creation of the Postgres service:

* `create_tables.sql` will create the database for development
* `create_test_database.sh` will create the database for testing

## Development environment scripts

All scripts should be run from the root of the repository.

`scripts/run_linter.sh` will run a Python linter and output the quality of the code.

`scripts/run_local.sh` will run the local Docker environment.

This script is a shortcut for `docker-compose -f docker-compose.yml -f docker-compose.development.yml`, appending the commandline arguments at the end of the call.

By default, it will run `up -d`, which will run all services in the background.

For instance, calling the script like this: `scripts/run_local.sh down` will be equivalent to running: `docker-compose -f docker-compose.yml -f docker-compose.development.yml down`.

`scripts/run_terminal.sh` will open a terminal session into the `web` container. Very useful to debug or to add new packages via `pip`.

`scripts/run_tests.sh` will run the test suite. 

## Build docker image

````
docker build -t hubmap/antibody-api:latest .
````

For building a released version of the image, specify the version tag:

````
docker build -t hubmap/antibody-api:0.1.0 .
````

## Publish the image to DockerHub

````
docker login
docker push hubmap/antibody-api:latest
````

For a released version of the image, specify the version tag:

````
docker build -t hubmap/antibody-api:0.1.0 .
````

## Deployment

For DEV/TEST/STAGE, no need to make changes to the `docker-compose.deployment.yml` and just use the `hubmap/antibody-api:latest` tag. 

For PROD, use the released version/tag like `hubmap/antibody-api:0.1.0` by specifying it in the `docker-compose.deployment.yml` before pulling the docker image and starting the container.

````
docker-compose -f docker-compose.deployment.yml up -d --no-build
````

## Redeployment

Will need to shut down the running container and remove the old image first:

````
docker-compose -f docker-compose.deployment.yml down --rmi all
````

Then download the new image and start up the container:

````
docker-compose -f docker-compose.deployment.yml up -d --no-build
````
