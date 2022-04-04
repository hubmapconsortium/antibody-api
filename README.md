# antibody-api

This information will help you get the Antibody API up in running whether locally or on an environment.

## Build, Publish, Deploy Workflow
These are the steps used to build, publish a Docker image, and then deploy it.

Before doing so you will need to follow the steps outlined in the section "Antibody API Configuration Changes"
to configure the server, and the instructions in the section
"Using the SearchAPI instead of directly reading from Elastic Search" to properly
configure the Search API server to handle queries from the Antibody API.

Local deployment instructions for testing purposes are found in the Section "Local Deployment".


### Get the Latest code
Login to the target machine and get the latest version of the code from the GitHub repository.
```bash
# Access the server, switch accounts and go to the server directory
$ ssh -i ~/.ssh/id_rsa_e2c.pem cpk36@ingest.dev.hubmapconsortium.org
$ sudo /bin/su - centos
$ cd hubmap/antibody-api
$ pwd
/home/centos/hubmap/antibody-api
$ git status
# On branch production
$ git pull
```
You should now have the most recent version of the code.

If there are any changes to the './instance/app.conf' file, make them now.

### Build Docker Image
In building the latest image specify the latest tag:
````bash
$ docker build -t hubmap/antibody-api:latest .
````

In building a release version of the image, specify the version tag:
````bash
$ docker build -t hubmap/antibody-api:0.1.0 .
````

### Publish the Image to DockerHub
Saving the image requires access to the DockerHub account with 'PERMISSION' 'Owner' account.
You may also see [DockerHub Antibody APi](https://hub.docker.com/repository/docker/hubmap/antibody-api).
To make changes you must login.
````bash
$ docker login
````

For DEV/TEST/STAGE, there is no need to make changes to the `docker-compose.deployment.yml` and just use the `hubmap/antibody-api:latest` tag.
````bash
$ docker push hubmap/antibody-api:latest
````

For PROD, use the released version/tag like `hubmap/antibody-api:0.1.0` by specifying it
in the `docker-compose.deployment.yml` before pulling the docker image and starting the container.
````bash
$ docker push hubmap/antibody-api:0.1.0
````
After you've created the numbered release (text after the colon above) you should save it in
the project [Release](https://github.com/hubmapconsortium/antibody-api/releases) page.

### Deploy the Saved Image
Deploy the image that you saved on GitHub by using the '--no-build' optional argument.
````bash
$ docker-compose -f docker-compose.deployment.yml up -d --no-build
````

### Examine Server Logs
To look at the logs of the running server, you may use.
```bash
$ tail -f server/log/uwsgi-antibody-api.log
```

## Redeployment

Will need to shut down the running container and remove the old image first:
````bash
$ docker-compose -f docker-compose.deployment.yml down --rmi all
````

Then download the new image and start up the container:
````bash
$ docker-compose -f docker-compose.deployment.yml up -d --no-build
````
The '--no-build' get's the container from DockerHub.

## Local Deployment

For local development you will also need to install the [Search API from GitHub](https://github.com/hubmapconsortium/search-api).
See "Using the SearchAPI instead of directly reading from Elastic Search" for configuration information.

Before deploying the server you will need to configure it.
Please follow the steps outlined in the section "Antibody API Configuration Changes"

To shutdown and remove all containers if anything is running by executing the following:
```bash
$ ./scripts/run_local.sh down -v --rmi all
```

Then restore the Docker Containers, Networks, and Volumes can be done by executing the following script.
If you delete one of the Docker images (say the "antibody-api_web-1 container) this will rebuild and restart it.
```bash
$ ./scripts/run_local.sh
```

You will need to manually create the tables on the PostgreSQL database that is running in the container.
The user, password, and database definitions are found in 'server/antibodyapi/default_config.py',
and for deployment should be overwritten in 'instance/app.conf' (which is not kept in the repo).
This is done by accessing the database through the command line 'psql' command.
```bash
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
```bash
if [[ `which curl; echo $?` -ne 0 ]] ; then
  brew install curl
fi
curl -H 'Content-Type: application/json' -X GET http://localhost:9200/hm_antibodies/_search?pretty
```

This should match the data in the database. Taking one of the "antibody_uuid" entries returned by Elastic Search above.
```bash
$ psql -h localhost -U postgres -d antibodydb -c "SELECT * from antibodies where antibody_uuid='ec53fcf7bf49db0a100ff5b218cf82a3'"
```

Once the data is loaded you can use the antibody search api located at [http://localhost:500/](http://localhost:5000)


## Deleting and Restoring the Elastic Search Index

The PostgreSQL database is used as the stable store for all of the data input,
and Elastic Search is used as a method to query it. If you need to move a database
from one server to another you can restore the Elastic Search Index as follows.
The following shows how to do this using the Docker containters spun up using
'./scripts/run_local.sh' (see './scripts/README.md for more information on these scripts).

First query on the index and see if data exists as follows:
```bash
$ curl -H 'Content-Type: application/json' -X GET http://localhost:9200/hm_antibodies/_search?pretty
```
You should get an error telling you that the index does not exist, or you should get data.

To test the restore, you can delete the Elastic Search Index using the following:
```bash
$ curl -H 'Content-Type: application/json' -X DELETE http://localhost:9200/hm_antibodies
```

Restore the Elastic Search Index from the PostgreSQL database using the 
MSAPI endpoint '/restore' on the antibody-api server as follows:
```bash
$ curl -H 'Content-Type: application/json' -X PUT http://localhost:5000/restore_elasticsearch
```

At this point the query on the Elastic Search index should return a subset of
the data found in the database (see ./scripts/compare_db_with_index.py)

## Using the SearchAPI instead of directly reading from Elastic Search

The file './server/antibodyapi/default_config.py' contains the variable 'QUERY_ELASTICSEARCH_DIRECTLY'.
If this variable is set to True, then searches from the UI will use Elastic Search directly.
If False then UI search queries will take place through the Search API.

The following describes how to set this up for testing.

### Search API Configuration Changes

search-api:src/instance/search-config.yaml: Add the following to the end of the file.
This will add the Antibody API Elastic Search index to Search API.
Note that the 'url' corresponds to the instance of ElasticSearch that is running in the Docker container.
For running in the various environments, set the 'url' appropriately.
```commandline
  hm_antibodies:
    active: true
    reindex_enabled: false
    public: hm_antibodies
    private: hm_antibodies
    elasticsearch:
      url: 'http://localhost:9200'
```

serch-api:/src/instance/app.cfg: The Elastic Search server should point to the instance running in Docker,
and the Entity API should be in the same space as the Antibody API; in this case 'test'.
You will also have to set the APP_CLIENT_ID, APP_CLIENT_SECRET, GLOBUS_HUBMAP_READ_GROUP_UUID,
GLOBUS_HUBMAP_DATA_ADMIN_GROUP_UUID appropriately.
These are not saved in GitHub for security reasons.
```commandline
ELASTICSEARCH_URL = 'http://localhost:9200'
ENTITY_API_URL = 'https://entity-api.test.hubmapconsortium.org'
```

### Startup the Search API on localhost

In the Search API repository consult the file './local-development-instructions.md'.
```bash
$ source venv-hm-search-api/bin/activate
$ python3 src/app.py
```

When you start the SearchAPI on localhost it will tell you what port it's running on in the console logs.
You will need this information to set the Antibody API SEARCH_API_BASE port below. 
```commandline
[2022-01-25 13:45:19] INFO in _internal:225:  * Running on http://10.0.0.14:5005/ (Press CTRL+C to quit)
```

### Antibody API Configuration Changes

antibody-api:/server/antibodyapi/default_config.py: Contains the variable 'QUERY_ELASTICSEARCH_DIRECTLY'.
If this variable is set to True, then searches from the UI will use Elastic Search directly.
If False then UI search queries will take place through the Search API.

You will need to specify the FLASK_APP_BASE_URI because of OAUTH2 redirection to the original application from the Gateway.

Use the local ELASTICSEARCH_SERVER, and SEARCH_API_BASE.
Set the UUID_API_URL (used to get the unique identifier for the antibodies),
and the INGEST_API_URL (used to store the .pdf files) the in test space (same space as Search API above).
Use 'host.docker.internal' to access the Search API running on localhost,
and the port from the INFO line above when the Search API is started (e.g., "Running on" port).

Make sure that both 'antibody-api:/instance/app.conf' and 'search-api/src/instance/app.cfg'
are using the same environment ('test' is suggested).
```commandline
FLASK_APP_BASE_URI = 'http://localhost:5000/'

# This is the name of the container in the docker-compose file.
ELASTICSEARCH_SERVER =   'http://elasticsearch'
SEARCH_API_BASE =        'http://host.docker.internal:5005'
UUID_API_URL =           'https://uuid-api.test.hubmapconsortium.org'
INGEST_API_URL =         'https://ingest-api.test.hubmapconsortium.org'

ANTIBODY_ELASTICSEARCH_INDEX = 'hm_antibodies'
QUERY_ELASTICSEARCH_DIRECTLY = False
```

### Startup the Antibody API processes in Docker

If you have not already started the Antibody API do so (see /scripts/README.md).


### Accessing the Search API from the container

You should be able to access the Search-API from the container with the following:
```bash
$ docker exec -it antibody-api_db_1 bash
$ apt update; apt install curl
$ curl -H 'Content-Type: application/json' -d '{"query": {"match_all": {}}}' -X POST  http://host.docker.internal:5005/hm_antibodies/search
{"_shards":{"failed":0,"skipped":0,"successful":1,"total":1}, ... , "timed_out":false,"took":1}
```

If you get an error message like below .
```bash
$ curl -H 'Content-Type: application/json' -d '{"query": {"match_all": {}}}' -X POST  http://host.docker.internal:5005/hm_antibodies/search
{"error":{"index":"hm_antibodies","index_uuid":"_na_","reason":"no such index [hm_antibodies]"
```
If you get this message you will need to load some data (see 'server/manual_test_files/README.md' section 'Manual test for 'upload' (.csv only)').

### Accessing the Antibody API GUI

Open the following web page
```commandline
http://localhost:5000
```
