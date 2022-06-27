# WineReviewsGraphing
Application to extract knowledge from unstructured data, process and load data into a Neo4j database, and then allow querying via a GUI.
The application can be run either directly on host or as a docker. If running as a docker there are also two ways, both require
execution of a bash script - one version uses docker run commands and the other uses docker-compose commands.

A) General notes about application: Please also see the presentation PDF file for walk through with screenshots.
1) Unstructured text is the "description" column of a wine reviews dataset from kaggle (CSV file from here: https://www.kaggle.com/zynicide/wine-reviews)
2) Python script 01_create_data_1.py will extract specified number of rows from the dataset and create individual text files.
3) Python script 02_load_neo_show_gui_3.py is used to process the text files and load data to Neo4j graph db. Then it displays
a GUI with tkinter to run preset queries and/or to upload new data (either as a path for a new text file OR as typed input).
3a) Features extracted: word count, sentence count, sentiment analysis, named entity recognition.
3b) Graph has three types of nodes: Review, Flavor, Entity
4) The github repo already has data from 1000 rows saved as text files. You can run only the script to load neo and show GUI without
running the first python script.

B) Running the application with Docker:
1) Two methods created to run the containers - one uses only "Docker Run" commands and other uses "Docker-compose" command
1a) Both methods use xhost to display GUI from within container on host display
1b) Create a temporary folder to mount volume for Neo4j db data
1c) Perform cleanup after running the application - remove temp folder, docker network, disable xhost permissions
2) Method 1: Docker Run version - bash script name: app_dockerRunVersion_1.sh
2a) Copy bash script into project folder
2b) Run with sudo permission: sudo ./app_dockerRunVersion_1.sh
3) Method 2: Docker-compose version - bash script name: app_dockerComposeVersion_1.sh
3a) Copy bash script and "dockerCompose_wineReviews_1.yaml" into project folder
3b) Run with sudo permission: sudo ./app_dockerComposeVersion_1.sh

C) Notes on running the python scripts locally:
1) 01_create_data_1.py:
1a) To extract data from CSV file for first 400 rows and thus create 400 individual text files, run script as:
python3 01_create_data_1.py -wineFileLoc './winemag-data-130k-v2.csv' -csvRowsLimit 400
2) 02_load_neo_show_gui_3.py:
2a) To process say only 300 of the potential 400 files:
python3 02_load_neo_show_gui_3.py -reloadNeo Y  -uploadLimit 300
2b) If running locally, you can also run without first clearing the Neo4j db, run script as:
python3 02_load_neo_show_gui_3.py -reloadNeo N
