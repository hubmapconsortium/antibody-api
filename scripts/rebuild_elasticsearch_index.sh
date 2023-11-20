#!/bin/sh

# Rebuild the ElasticSearch index
#
# Login through the UI to get the credentials for the environment that you are using, e.g.:
# https://ingest.dev.hubmapconsortium.org/ (DEV)
# https://ingest.test.hubmapconsortium.org/ (TEST)
#
# In Firefox (Tools > Browser Tools > Web Developer Tools).
# Click on "Storage" then the dropdown for "Local Storage" and then the url,
# Take the 'groups_token' as the TOKEN below...
#
# When calling specify the ANTIBODY_URL and the TOKEN, e,g.:
#export ANTIBODY_URL="http://localhost:5000" ; export TOKEN="tokenString" ; scripts/rebuild_elesticsearch_index.sh
#export ANTIBODY_URL="https://avr.dev.hubmapconsortium.org" ; export TOKEN="tokenString" ; scripts/rebuild_elesticsearch_index.sh
#
# if it works you will get: {"antibodies":[]}

curl --request PUT \
 --url "${ANTIBODY_URL}/restore_elasticsearch" \
 --header "Content-Type: application/json" \
 --header "Accept: application/json" \
 --header "Authorization: Bearer $TOKEN"
