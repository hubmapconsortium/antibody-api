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
docker push -t hubmap/antibody-api:0.1.0 .
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
