#!/bin/sh

## Script to start the necessary containers using Docker Run version of commands.
## IMPORTANT: Copy this to you local machine in the project folder and make as executable:
# chmod +x ./app_dockerRunVersion_1.sh
## Run it with sudo priveleges
# sudo ./app_dockerRunVersion_1.sh

## enable xhost communication
echo "\nEnabling xhost communication"
xhost +
#xhost +local:root

## setup docker a new network
echo "\nRemoving docker network at startup and creating new one: testappnetwork"
docker network rm testappnetwork
sleep 5
docker network create testappnetwork

## run neo4j container
## Note: also creates a directory for the volume for neo4j db
#echo "\nStarting neo4j container in detach mode"
docker run --detach --rm -e NEO4J_AUTH=neo4j/cba -v $(pwd)/tempneo4j/data:/var/lib/neo4j/data:rw --net testappnetwork --name contneo4j410 rbewoor/myneo4j410nocmd:1.0

## sleep to ensure neo4j container starts up completely
SLEEP_TIME_BEFORE_APP_START=30
echo "\nStarted sleeping for $SLEEP_TIME_BEFORE_APP_START seconds to allow neo4j container startup..."
sleep $SLEEP_TIME_BEFORE_APP_START
echo "\nEnded sleeping for $SLEEP_TIME_BEFORE_APP_START seconds..."

## run app container
## Note: uses the X11 host for display
echo "\nStarting App container....\n\n"
docker run --rm -e NEO4J_CONTAINER_NAME=contneo4j410 -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:rw --net testappnetwork --name contwinereviewapp rbewoor/winereviewapp:1.0

## stop all running containers - make sure neo4j container stops
echo "\nRunning command to stop all running containers...."
docker stop $(docker ps -q)
echo "\nStopped all running containers...."

## remove docker network
echo "\nRemoving docker network: testappnetwork"
docker network rm testappnetwork

## remove the volume for neo4j db
echo "\nRemoving the tempneo4j folder (used for neo4j db data volume)"
rm -r $(pwd)/tempneo4j

## disable xhost communication
echo "\nDisabling xhost communication"
xhost -
#xhost -local:root

echo "\nScript finished."