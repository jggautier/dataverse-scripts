#!/bin/bash

# Script for replacing the metadata of datasets in a given dataverse and in that dataverse's sub-dataverses. 
# A new draft dataset version of each dataset will be created but not published.
# Software dependencies: You'll need to download jq (https://stedolan.github.io/jq).
# Limitations: 
	# The metadata of unpublished datasets and datasets whose only version is deaccessioned won't be changed since the Search API retrieves PIDs of the only most recently published dataset versions. 
	# You may need to give yourself execute privileges to run execute this file. In your terminal, run chmod u+x delete_all_datasets_in_a_dataverse.command
	# This script doesn't publish the new version of the dataset. (I think publising draft dataset versions can be done in bulk with APIs.)

token="8dc13e88-0488-4a65-9466-2f0ce78c6dca" # Enter super-user's Dataverse account API token.
server="https://demo.dataverse.org" # Enter name of server url, which is home page URL of the Dataverse installation, e.g. https://demo.dataverse.org
alias="juliangautier" # Enter alias of dataverse. E.g. sonias-dataverse.
metadatafile="replacementmetadata.json" # Enter name of json file that contains replacement metadata, e.g. replacementmetadata.json

# This changes the directory to whatever directory this .command file is in, so that deleted_datasetPIDs_in_$alias.txt is saved in that directory.
cd "`dirname "$0"`"

# This uses the Search API and jq to retrieve the persistent IDs (global_id) of datasets in the dataverse. Then it stores the persistent IDs in a text file on the user's computer.
# Change the per_page parameter to retrieve more persistent IDs.
curl "$server/api/search?q=*&subtree=$alias&per_page=50&type=dataset" | jq -r '.data.items[].global_id' > dataset_metadata_replaced_in_$alias.txt

# This loops through the stored persistent IDs, replaces the metadata of those datasets with the metadata in your metadata file, and creates and publishes a new version for each dataset.
for global_id in $(cat dataset_metadata_replaced_in_$alias.txt);
do
	curl -H "X-Dataverse-key: $token" -X PUT "$server/api/datasets/:persistentId/editMetadata?persistentId=$global_id&replace=true" --upload-file $metadatafile

done

# This publishes the draft dataset versions as minor versions. Change type=minor to type=major to publish major versions instead.
for global_id in $(cat dataset_metadata_replaced_in_$alias.txt);
do
	curl -H X-Dataverse-key:$token -X POST "$server/api/datasets/:persistentId/actions/:publish?persistentId=$global_id&type=minor"
done

exit
