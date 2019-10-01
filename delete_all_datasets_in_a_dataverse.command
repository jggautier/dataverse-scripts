#!/bin/bash

# Script for destroying datasets in a dataverse and in any of the dataverses nested in that dataverse.
# Software dependencies: You'll need to download jq (https://stedolan.github.io/jq).
# Limitations:
	# Mac OS bias: The script has been tested only on Mac OS and instructions may not be helpful for use in other operating systems.
	# Unpublished datasets: Unpublished datasets and datasets whose only version is deaccessioned won't be destroyed since the Search API retrieves PIDs of the only most recently published dataset versions. 
	# Linked datasets: If the API Token belongs to an account that has edit access to any datasets that are linked in the given dataverse, those datasets will also be destroyed.
	# Getting this .command file to work: You may need to give yourself execute privileges to execute this file. In your terminal, run chmod u+x delete_all_datasets_in_a_dataverse.command

token="ENTER_API_TOKEN" # Enter super-user's Dataverse account API token.
server="ENTER_SERVER_URL" # Enter name of server url, which is home page URL of the Dataverse installation, e.g. https://demo.dataverse.org
alias="ENTER_DATAVERSE_ALIAS" # Enter alias of dataverse. E.g. sonias-dataverse.

# This changes the directory to whatever directory this .command file is in, so that deleted_datasetPIDs_in_$alias.txt is saved in that directory.
cd "`dirname "$0"`"

# This uses the Search API and jq to retrieve the persistent IDs (global_id) of datasets in the dataverse. Then it stores the persistent IDs in a text file on the user's computer.
# Change the per_page parameter to retrieve more persistent IDs.
curl "$server/api/search?q=*&subtree=$alias&per_page=50&type=dataset" | jq -r --arg alias "$alias" '.data.items | map(select(.identifier_of_dataverse==$alias))[].global_id' > deleted_datasetPIDs_in_$alias.txt

# This loops through the stored persistent IDs and destroys those datasets
for global_id in $(cat deleted_datasetPIDs_in_$alias.txt);
do
	curl -H "X-Dataverse-key:$token" -X DELETE $server/api/datasets/:persistentId/destroy/?persistentId=$global_id
done
exit
