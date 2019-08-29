#!/bin/bash

# This works only for files that have persistent IDs.

token="API TOKEN HERE"

# Create a folder in the directory
output="name_of_folder/"

# To-do: Adjust to use file's database id instead of persistent ID. (Some Dataverse installations don't register PIDs for files.)

# Uses jq to gets the PIDS and names of files in the specified dataset
curl -H "X-Dataverse-key: $token" SERVER_URL_HERE/api/datasets/:persistentId/versions/1/files?persistentId=doi:DATASET_DOI_HERE | tee >(jq '.data[].dataFile.persistentId' >persistentid) >(jq '.data[].dataFile.filename' >filenames) 

# Turns those file PIDs and names into arguments
paste persistentid filenames > arg 

# Uses those arguments to construct wget commands to download the dataset's files
cat arg | xargs -L1 bash -c ' wget -O '$output'$1 -P '$output' SERVER_URL_HERE/api/access/datafile/:persistentId?persistentId=$0' 

# Not yet sure what this line does...
rm filenames persistentid arg