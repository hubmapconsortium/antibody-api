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

To shutdown and remove all containers if anything is running by executing the following:
```commandline
./scripts/run_local.sh down -v --rmi all
```

Then restore the Docker Containers, Networks, and Volumes by executing the following:
```commandline
./scripts/run_local.sh
```

You will need to manually create the tables on the PostgreSQL database that is running in the container.
The user, password, and database definitions are found in 'server/antibodyapi/default_config.py',
and for deployment should be overwritten in 'instance/app.conf' (which is not kept in the repo).
This is done by accessing the database through the command line 'psql' command.
```commandline
if [[ `which psql; echo $?` -ne 0 ]] ; then
  brew install postgresql
fi
psql -h localhost -U postgres -d antibodydb -a -f ./development/postgresql_init_scripts/create_tables.sql 
```

Now that the tables exist, you will need to load some data into them.
Find the file 'server/manual_test_files/README.md', and execute the sequence in the 'Manual test for 'upload' (.csv only)' section.
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
The following shows how to do this using the Docker containters spun up using
'./scripts/run_local.sh' (see './scripts/README.md for more information on these scripts).

First query on the index and see if data exists as follows:
```commandline
curl -H 'Content-Type: application/json' -X GET http://localhost:9200/hm_antibodies/_search?pretty
```
You should get an error telling you that the index soes not exist, or you should get data.

To test the restore, you can delete the Elastic Search Index using the following:
```commandline
curl -H 'Content-Type: application/json' -X DELETE http://localhost:9200/hm_antibodies
```

Restore the Elastic Search Index from the PostgreSQL database using the 
MSAPI endpoint '/restore' on the antibody-api server as follows:
```commandline
curl -H 'Content-Type: application/json' -X PUT http://localhost:5000/restore
```

At this point the query on the Elastic Search index should return a subset of
the data found in the database (see ./scripts/compare_db_with_index.py)

## Using the SearchAPI instead of directly reading from Elastic Search

The file './server/antibodyapi/default_config.py' contains the variable 'QUERY_ELASTICSEARCH_DIRECTLY'.
If this variable is set to True, then searches from the UI will use Elastic Search directly.
If False then UI search queries will take place through the Search API.

The following describes how to set this up for testing.

### Setup to use the Search API

Set the following variable in './server/antibodyapi/default_config.py' as follows:
```commandline
    QUERY_ELASTICSEARCH_DIRECTLY = False
```

Make sure that both 'antibody-api:/instance/app.conf' and 'search-api/src/instance/app.cfg'
are using the same environment ('test' is suggested).

search-api/src/instance/app.cfg: use the Elastic Search in the container, and Entity Api in test.
```commandline
    ELASTICSEARCH_URL =      'http://localhost:9200'
    ENTITY_API_URL =         'https://entity-api.test.hubmapconsortium.org'
```

When you start the SearchAPI it will tell you what port it's running on in the console logs:
```commandline
[2022-01-25 13:45:19] INFO in _internal:225:  * Running on http://10.0.0.14:5005/ (Press CTRL+C to quit)
```

antibody-api:/instance/app.conf: use the local Search API, Entity API and UUID_API in test.
Use 'host.docker.internal' on the above port to access the Search API.
```commandline
    SEARCH_API_BASE =        'http://host.docker.internal:5005'
    ENTITY_API_BASE =        'https://entity-api.test.hubmapconsortium.org'
    UUID_API_URL =           'https://uuid-api.test.hubmapconsortium.org'
    ELASTICSEARCH_SERVER =   'http://elasticsearch'
    ANTIBODY_ELASTICSEARCH_INDEX = 'hm_antibodies'
    QUERY_ELASTICSEARCH_DIRECTLY = False
```

### Add the Antibody API Elastic Search index to Search API

Add the following to the end of the file 'search-api:src/instance/search-config.yaml'.
```commandline
  hm_antibodies:
    active: true
    public: hm_antibodies
    private: hm_antibodies
    document_source_endpoint: 'Doesn''t use this'
    elasticsearch:
      url: 'http://localhost:9200'
      mappings: "addl_index_transformations/portal/config.yaml"
    transform:
      module: elasticsearch.addl_index_transformations.portal
```

### Startup the Search API on localhost

In the Search API repository consult the file './local-development-instructions.md'.
```commandline
source venv-hm-search-api/bin/activate
python3 src/app.py
```

### Accessing the Search API from the container

You should be able to access the Search-API from the container with the following:
```commandline
docker exec -it antibody-api_db_1 bash
apt update; apt install curl
curl -H 'Content-Type: application/json' -d '{"query": {"match_all": {}}}' -X POST  http://host.docker.internal:5005/hm_antibodies/search
{"_shards":{"failed":0,"skipped":0,"successful":1,"total":1}, ... , "timed_out":false,"took":1}
```

If you get an error message like below then you will need to load some data (see 'server/manual_test_files/README.md' section 'Manual test for 'upload' (.csv only)')
```commandline
curl -H 'Content-Type: application/json' -d '{"query": {"match_all": {}}}' -X POST  http://host.docker.internal:5005/hm_antibodies/search
{"error":{"index":"hm_antibodies","index_uuid":"_na_","reason":"no such index [hm_antibodies]"
```