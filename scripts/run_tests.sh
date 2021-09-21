#!/bin/bash
docker-compose -f docker-compose.yml -f docker-compose.development.yml run --rm web sh -c "pip install -e . && pytest -v --random-order ${@}"
