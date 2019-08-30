#!/bin/bash

# File hierarchy: This does not reconstruct any folder hierarchy that the files may be in. The files are listed as flat. Retaining file hierarchy should be possible with additional API calls...
# Restricted files: If API token belongs to Dataverse account that has no permissions to download restricted files in the dataset, files will be created, but they will be empty.
# Software dependencies: You'll need to download jq (https://stedolan.github.io/jq) and wget (https://www.gnu.org/software/wget).

# User enters her Dataverse account API token.
token="API_TOKEN"

output="OUTPUT_FOLDER_NAME" # Creates a folder in your terminal's active directory and enter name of folder, e.g. dataverse_files
server="SURVER_URL" # Enter name of server url, which is home page URL of the Dataverse installation, e.g. https://dataverse.harvard.edu
datasetPID="DATASET_PID" # Enter dataset persistent identifier, e.g. doi:10.12345/AA1/123456

# This uses jq to get the dataset's file database IDs and names from the dataset metadata. 
# SURVER_URL must be changed to the home page URL of the Dataverse installation, e.g. https://dataverse.harvard.edu
curl -H "X-Dataverse-key: $token" $server/api/datasets/:persistentId/versions/1/files?persistentId=$datasetPID | tee >(jq '.data[].dataFile.id' >fileid) >(jq '.data[].dataFile.filename' >filenames) 

# This turns those file IDs and names into arguments.
paste fileid filenames > arg 

# This uses those arguments to construct wget commands to download the dataset's files. Remove the parameter "format=original" to instead download the archive versions of any ingested tabular files.
cat arg | xargs -L1 bash -c ' wget -O '$output''/'$1 -P '$output' '/' '$server'/api/access/datafile/$0?format=original'

# This removes the files that the script created in the terminal's active directory
rm filenames fileid arg
