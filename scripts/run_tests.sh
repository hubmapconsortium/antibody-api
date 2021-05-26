#!/bin/bash
docker-compose -f docker-compose.yml -f docker-compose-test.yml run --rm web sh -c "pip install -e . && pytest -v"
docker-compose -f docker-compose.yml -f docker-compose-test.yml down -v
