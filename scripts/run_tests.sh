#!/bin/bash
docker-compose run --rm web sh -c "pip install -e . && pytest -v"
