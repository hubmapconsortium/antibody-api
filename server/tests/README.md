# Tests

The tests are run using [pytest](https://buildmedia.readthedocs.org/media/pdf/pytest/latest/pytest.pdf).
There is one test file 'tests/test_app.py' which includes other test files located in subdirectories of the 'tests'
directory. By convention pytest will assume that any file that matches 'test_*.py' is a test file and it will run it.

# Running the tests

### In a Docker Image

The file (./scripts/run_tests.sh) will run the tests (all without any parameters) in './server/tests' in a Docker image and display the results.
```bash
$ ./development/postgresql_init_scripts/create_test_database.sh
$ python3 -m pip install --upgrade pip
$ rm -rf ./server/.pytest_cache/
$ ./scripts/run_tests.sh
```

This is what you add to run_tests.sh select a test: "-k test_post_csv_file_with_pdf_should_save_those_correctly"

#### Locally

To run the tests locally, do the following:

```bash
$ cd server
$ python3 -m pip install --upgrade pip
$ rm -rf venv
$ python3 -m venv venv
$ pip install -r ../requirements.txt
$ pip install fpdf
$ source venv/bin/activate
$ PYTHONPATH=. pytest -v
```

To run a specific test
```bash
$ source venv/bin/activate
$ PYTHONPATH=. pytest -v tests/test_app.py::TestGetAntibodies::test_should_return_a_200_response
$ PYTHONPATH=. pytest -v tests/test_app.py::TestGetAntibodies::test_all_antibody_fields_are_retrieved_correctly
```
