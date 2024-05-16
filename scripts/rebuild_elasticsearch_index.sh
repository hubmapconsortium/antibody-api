#!/bin/sh

# Rebuild the ElasticSearch index
#
# Login through the UI to get the credentials for the environment that you are using, e.g.:
# https://ingest.dev.hubmapconsortium.org/ (DEV)
# https://ingest.test.hubmapconsortium.org/ (TEST)
# https://ingest.hubmapconsortium.org/ (PROD)
#
# In Firefox (Tools > Browser Tools > Web Developer Tools).
# Click on "Storage" then the dropdown for "Local Storage" and then the url,
# Take the 'groups_token' as the TOKEN below...
#
# When calling specify the TOKEN, e,g.:
#export TOKEN="tokenString" ; ./scripts/rebuild_elasticsearch_index.sh ANTIBODY_URL
#
# if it works you will get: {"antibodies":[]}

echo "Rebuild the ElasticSearch index..."

ANTIBODY_URL_LOCAL='https://localhost:5000'
ANTIBODY_URL_DEV='https://avr.dev.hubmapconsortium.org'
ANTIBODY_URL_TEST='https://avr.test.hubmapconsortium.org'
ANTIBODY_URL_PROD='https://avr.hubmapconsortium.org'
ANTIBODY_URL=$1
echo "ANTIBODY_URL==$ANTIBODY_URL"

curl --request PUT \
 --url "${ANTIBODY_URL}/restore_elasticsearch" \
 --header "Content-Type: application/json" \
 --header "Accept: application/json" \
 --header "Authorization: Bearer $TOKEN"
