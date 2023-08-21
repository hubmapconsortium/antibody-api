#!/bin/sh

ANTIBODY_URL='https://avr.dev.hubmapconsortium.org'

# Rebuild the ElasticSearch index
#
# To get the BEARER_TOKEN, login through the UI (https://ingest.hubmapconsortium.org/) to get the credentials...
# In Firefox open 'Tools > Browser Tools > Web Developer Tools'.
# Click on "Storage" then the dropdown for "Local Storage" and then the url,
# Applications use the "groups_token" from the returned information.
# UI times-out in 15 min so close the browser window, and the token will last for a day or so.
#
# Run this with....
# export TOKEN="xxx"; ./scripts/restore_es_dev.sh

curl --request PUT \
 --url "${ANTIBODY_URL}/restore_elasticsearch" \
 --header "Content-Type: application/json" \
 --header "Accept: application/json" \
 --header "Authorization: Bearer $TOKEN"
