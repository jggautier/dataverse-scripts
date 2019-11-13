#!/bin/bash

# Script for replacing specific metadata of datasets in a given dataverse. This script creates and publishes a new dataset version for each dataset. After making edits to this .command file, double click it to run it.
# Software dependencies: You'll need to download jq (https://stedolan.github.io/jq).
# Metadata json file: This script uses an API that looks for metadata in a JSON file. For guidance on how to format the json file, see http://guides.dataverse.org/en/latest/api/native-api.html#edit-dataset-metadata
# Getting this .command file to work: You may need to give yourself execute privileges to execute this file. In your terminal, run chmod u+x replace_dataset_metadata_in_a_dataverse.command
# Limitations:
	# Mac OS bias: The script has been tested only on Mac OS and instructions may not be helpful for use in other operating systems.
	# Unpublished datasets: The metadata of unpublished datasets and datasets whose only version is deaccessioned won't be changed since the Search API does not yet retrieve the persistent identifiers of those datasets. 

token="ENTER_API_TOKEN" # Enter API token of Dataverse account that has edit and publish privileges on the datasets.
server="ENTER_SERVER" # Enter name of server url, which is home page URL of the Dataverse installation, e.g. https://demo.dataverse.org
alias="ENTER_DATAVERSE_ALIAS" # Enter alias of dataverse. E.g. sonias-dataverse would be the alias of a dataverse with the URL https://demo.dataverse.org/dataverse/sonias-dataverse

# Enter name of a json file that contains the replacement metadata. Make sure the file is in the same directory (e.g. your desktop) as this .command file.
# Include the .json extension, e.g. replacementmetadata.json
metadatafile="ENTER_FILE_NAME.json"

# This changes the directory to whatever directory this .command file is in, so that the script knows where to find the metadata JSON file and the dataset_metadata_replaced_in_$alias.txt file is saved in that directory.
cd "`dirname "$0"`"

# This uses Dataverse's Search API and jq to retrieve the persistent IDs (global_id) of datasets in the dataverse. Then it stores the persistent IDs in a text file on the your computer.
# Change the per_page parameter (i.e. per_page=50) to retrieve more persistent IDs, up to 1000 PIDs.
curl "$server/api/search?q=*&subtree=$alias&per_page=50&type=dataset" | jq -r --arg alias "$alias" '.data.items | map(select(.identifier_of_dataverse==$alias))[].global_id' > dataset_metadata_replaced_in_$alias.txt

# This loops through the stored persistent IDs, removes any carriage return characters at the ends of those IDs, and replaces the metadata of those datasets with the metadata in your metadata file.
for global_id in $(cat dataset_metadata_replaced_in_$alias.txt);
do
	global_id=${global_id%$'\r'} # If any lines in the text file contains carriage returns, this removes those carriage returns.
	curl -H "X-Dataverse-key: $token" -X PUT "$server/api/datasets/:persistentId/editMetadata?persistentId=$global_id&replace=true" --upload-file $metadatafile
done

# This publishes the draft dataset versions as minor versions. Change type=minor to type=major to publish major versions instead.
for global_id in $(cat dataset_metadata_replaced_in_$alias.txt);
do
	global_id=${global_id%$'\r'} # If any lines in the text file contains carriage returns, this removes those carriage returns.
	curl -H X-Dataverse-key:$token -X POST "$server/api/datasets/:persistentId/actions/:publish?persistentId=$global_id&type=minor"
done

exit
