#!/bin/bash

# Software dependencies: You'll need to download jq (https://stedolan.github.io/jq) and wget (https://www.gnu.org/software/wget).
# File hierarchy: This does not reconstruct any folder hierarchy that the files may be in. The files are listed as flat. Retaining file hierarchy should be possible with additional API calls...
# Restricted files: If the dataset has any restricted files, files will be created but they will be empty.
# Original file formats: Original file formats of any ingested tabular files are downloaded, but are given the file name and file extension of the archived (.tab) file.

token="API_TOKEN" # Enter downloader's Dataverse account API token.
output="OUTPUT_FOLDER_NAME" # Create a folder in your terminal's active directory and enter name of that folder, e.g. dataverse_files
server="SERVER_URL" # Enter name of server url, which is home page URL of the Dataverse installation, e.g. https://dataverse.harvard.edu
datasetPID="DATASET_PID" # Enter dataset persistent identifier, e.g. doi:10.12345/AA1/123456

# This uses jq to get the dataset's file database IDs and names from the dataset metadata. 
curl -H "X-Dataverse-key: $token" $server/api/datasets/:persistentId/versions/1/files?persistentId=$datasetPID | tee >(jq '.data[].dataFile.id' >fileid) >(jq '.data[].dataFile.filename' >filenames) 

# This turns those file IDs and names into arguments.
paste fileid filenames > arg 

# This uses those arguments to construct wget commands to download the dataset's files. Remove the parameter "format=original" to instead download the archive versions of any ingested tabular files.
cat arg | xargs -L1 bash -c ' wget -O '$output''/'$1 -P '$output' '/' '$server'/api/access/datafile/$0?format=original'

# This removes the files that the script created in the terminal's active directory
rm filenames fileid arg
