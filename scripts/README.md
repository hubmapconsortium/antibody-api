# Scripts

There are scripts for running, testing, linting, and establishing a shell to a Docker container.
There is also a script for building/updating the API generated from the OpenAPI spec.

## OpenAPI Script

The script './scripts/build_openapi_client.sh' will create/update the client API from the OpenAPI
specification located at './antibody-api-spec.yml'. The client will be built in the 'hu-bap-antibody-api-client' directory.

## Docker Scripts
These scripts package the docker "magic".  They must be run from the repo root folder.

They all startup Docker containers locally, and so they all need Docker to be running locally.

### Linter

This will run the python linter over the python code and displays the quality.

### Local

This will start the service locally.
The server will be available on [http://localhost:5000](http://localhost:5000).
Before it can be run the 'instance/app.conf' file must be configured (see ./README.md) as the server makes connections to the services to get a UUID and also to store the .pdf (see ./scrpts/README.md).

While many containers are created by the 'docker-compose.development.yml' file, the local environment depends on services mentioned in the '/instance/app.conf' file (see ./README.md); to get a UUID and also to store the .pdf (see ./scrpts/README.md).
In particular, the UUID_API_URL is used to get the unique identifier for the antibodies, and
the INGEST_API_URL is used to store the .pdf files.

This local script also has a default command that allows you to run any command that you want.
If you add a parameter to the end then it will run that parameter.
By default, it will run 'up -d' which daemonizes it and hides it from your view.
Scenario, './scripts/run_local.sh up' will not daemonize (add the '-d').
You can also bring the server down with  './scripts/run_local.sh down'

You should note that the database tables need to be created before the first
time that you access the GUI. For setup from scratch, please see 'README.md'
section 'Deployment Locally'.

### Terminal

This will create a container for the web service ONLY and will open a terminal session for it.

The use case for this is, if you want to add a library inside a container to get a new requirements file (i.e. with 'pip freese').

### Tests

This (./scripts/run_tests.sh) will run the tests (all without any parameters) in './server/tests' and display the results.

This is what you add to select a test: "-k test_post_csv_file_with_pdf_should_save_those_correctly"
