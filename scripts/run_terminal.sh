#!/bin/bash

docker-compose -f docker-compose.yml -f docker-compose.development.yml run --rm --entrypoint "/bin/sh" web
