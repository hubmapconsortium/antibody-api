# antibody-api

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
docker push -t hubmap/antibody-api:0.1.0
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

## Deployment Locally

To shutdown and remove all containers if anything is running execute the following:
```commandline
./scripts/run_local.sh down -v --rmi all
```

Then start things up which will restore the Docker Containers, Networks, and Volumes.
```commandline
./scripts/run_local.sh
```

You will need to manually create the tables on the PostgreSQL database that is running in the container.
The user, password, and database definitions are found in 'server/antibodyapi/default_config.py',
and for deployment should be overwritten in 'instance/app.conf' (which is not kept in the repo).
This is donw by accessing the database through the command line 'psql' command.
```commandline
if [[ `which psql; echo $?` -ne 0 ]] ; then
  brew install postgresql
fi
psql -h localhost -U postgres -d antibodydb -a -f ./development/postgresql_init_scripts/create_tables.sql 
```

Now that the tables exist, you will need to load some data into them.
Fine the file 'server/manual_test_files/README.md', and execute the sequence in the 'Manual test for 'upload' (.csv only)' section.
This will upload the data to the PostgreSQL database and to Elastic Search.

To see the data that is in Elastic Search directly you can execute the following.
The index (here 'hm_antibodies') is defined in 'server/antibodyapi/default_config.py' as ANTIBODY_ELASTICSEARCH_INDEX.
```commandline
if [[ `which curl; echo $?` -ne 0 ]] ; then
  brew install curl
fi
curl -H 'Content-Type: application/json' -X GET http://localhost:9200/hm_antibodies/_search?pretty
```

This should match the data in the database. Taking one of the "antibody_uuid" entries returned by Elastic Search above.
```commandline
psql -h localhost -U postgres -d antibodydb -c "SELECT * from antibodies where antibody_uuid='ec53fcf7bf49db0a100ff5b218cf82a3'"
```

Once the data is loaded you can use the antibody search api located at [http://localhost:500/](http://localhost:5000)

## Deleting and Restoring the Elastic Search Index

The PostgreSQL database is used as the stable store for all of the data input,
and Elastic Search is used as a method to query it. If you need to move a database
from one server to another you can restore the Elastic Search Index as follows.

If you need to delete the Elastic Search Index you can use
```commandline
curl -H 'Content-Type: application/json' -X DELETE http://localhost:9200/hm_antibodies
```

You can restore the Elastic Search Index from the PostgreSQL database using the 
MSAPI endpoint '/restore' on the antibody-api server as follows:
```commandline
curl -H 'Content-Type: application/json' -X PUT http://localhost:5000/restore
```
