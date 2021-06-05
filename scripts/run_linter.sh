#!/bin/bash
docker-compose -f docker-compose.yml -f docker-compose.development.yml run --rm --no-deps web sh -c "pylint --exit-zero antibodyapi/ tests/"
