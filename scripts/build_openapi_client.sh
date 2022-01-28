#!/bin/sh

echo "Building Python Client..."

# https://pypi.org/project/openapi-python-client/
if [[ ! -x `which openapi-python-client` ]] ; then
  echo "Installing openapi-python-client"
  pip install openapi-python-client
fi

CLIENT_DIR=./hu-bmap-antibody-api-client
ACTION='generate'
if [[ -d $CLIENT_DIR ]] ; then
  ACTION='update'
fi
openapi-python-client $ACTION --path antibody-api-spec.yaml
echo "Done!"