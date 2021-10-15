#!/bin/sh

## Script to start the necessary containers using Docker-compose version of commands.
## IMPORTANT: Copy this to you local machine in the project folder and make as executable:
# chmod +x ./app_dockerComposeVersion_1.sh
## Run it with sudo priveleges
# sudo ./app_dockerComposeVersion_1.sh
## Ensure the yaml compose file is in the same folder as this script: dockerCompose_wineReviews_1.yaml

## enable xhost communication
echo "\nEnabling xhost communication"
xhost +
#xhost +local:root

## no need to explicitly setup docker network here as docker-compose will do it automatically

## start the container for Neo4j with docker-compose
## Note: also creates a directory for the volume for neo4j db
echo "\nStarting up container for Neo4j in detach mode"
docker-compose -f $(pwd)/dockerCompose_wineReviews_1.yaml up -d contneo4j410

## sleep to ensure Neo4j container starts up completely
SLEEP_TIME_BEFORE_APP_START=10
echo "\nStarted sleeping for $SLEEP_TIME_BEFORE_APP_START seconds to allow Neo4j container startup..."
sleep $SLEEP_TIME_BEFORE_APP_START
echo "\nEnded sleeping for $SLEEP_TIME_BEFORE_APP_START seconds..."

## start the container for App with docker-compose
## Note: uses the X11 host for display
echo "\nStarting up container for App...."
docker-compose -f $(pwd)/dockerCompose_wineReviews_1.yaml up contwinereviewapp

## down the containers
echo "\nStopping (with docker-compose down) containers for Neo4j and App...."
docker-compose -f $(pwd)/dockerCompose_wineReviews_1.yaml down

## remove volumes
COUNT_VOLS_BEFORE=$(docker volume ls | wc -l)
echo "\nCount before volume cleanup = $COUNT_VOLS_BEFORE"
echo "\nRunning command to remove volumes...."
docker volume rm $(docker volume ls -q)
echo "\nRemoved all volumes...."
COUNT_VOLS_AFTER=$(docker volume ls | wc -l)
echo "\nCount after volume cleanup = $COUNT_VOLS_AFTER"

## remove the volume for neo4j db
echo "\nRemoving the tempneo4j folder (used for neo4j db data volume)"
rm -r $(pwd)/tempneo4j

## disable xhost communication
echo "\nDisabling xhost communication"
xhost -
#xhost -local:root

echo "\nScript finished."