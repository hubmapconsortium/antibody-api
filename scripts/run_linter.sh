#!/bin/bash
docker-compose run --rm --no-deps web sh -c "pylint --exit-zero ontologyapi/ tests/"
