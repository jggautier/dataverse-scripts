#!/bin/bash

# This does not reconstruct any folder hierarchy that the files may be in. The files are listed as flat. Retaining file hierarchy should be possible with additional API calls...
# Restricted files: If API token belongs to Dataverse account that has no permissions to download restricted files in the dataset, files will be created, but they will be empty.

# Software dependencies: You'll need to download jq (https://stedolan.github.io/jq) and wget (https://www.gnu.org/software/wget).

# User enters her Dataverse account API token.
token="API_TOKEN"

# User creates a folder in her terminal's active directory and enters name of folder.
output="NAME_OF_FOLDER_FOR_FILES/"

# This uses jq to get the dataset's file database IDs and names from the dataset metadata. 
# SURVER_URL must be changed to the home page URL of the Dataverse installation, e.g. https://dataverse.harvard.edu
curl -H "X-Dataverse-key: $token" SERVER_URL/api/datasets/:persistentId/versions/1/files?persistentId=doi:10.70122/FK2/O13BQC | tee >(jq '.data[].dataFile.id' >fileid) >(jq '.data[].dataFile.filename' >filenames) 

# This turns those file IDs and names into arguments.
paste fileid filenames > arg 

# This uses those arguments to construct wget commands to download the dataset's files. Remove the parameter "format=original" to instead download the archive versions of any ingested tabular files.
cat arg | xargs -L1 bash -c ' wget -O '$output'$1 -P '$output' SERVER_URL/api/access/datafile/$0?format=original'

# Not yet sure what this line does...
rm filenames fileid arg