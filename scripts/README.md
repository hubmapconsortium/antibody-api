# Scripts

These scripts package the docker "magic".
They must be run from the repo root

They all startup Docker containers locally, and so they all need Docker to be running locally.

## Linter

This will run the python linter over the python code and displays the quality.

## Local

This will start the service locally.
The server will be available on [http://localhost:5000](http://localhost:5000)

This local script also has a default command that allows you to run any command that yuo want.
If you add a parameter to the end then it will run that parameter.
By default it will run 'up -d' which deamonizes it and hides it from your view.
Scenario, './scripts/run_local.sh up' will not deamonize (add the '-d').
You can also bring the server down with  './scripts/run_local.sh down'

## Terminal

This will create a container for the web service ONLY and will open a terminal session for it.

The use case for this is, if you want to add a library inside a container to get a new requirements file (i.e. with 'pip freese').

## Tests

This (./scripts/run_tests.sh) will run the tests (all without any parametes) in './server/tests' and display the results.

This is what you add to select a test: "-k test_post_csv_file_with_pdf_should_save_those_correctly"
