#!/bin/bash

# Script for changing citation dates of datasets in a dataverse or for reverting those changes.
# Software dependencies: You'll need to download jq (https://stedolan.github.io/jq).
# Limitations: The citation dates of unpublished datasets and datasets whose only version is deaccessioned won't be changed since the Search API retrieves PIDs of the only most recently published dataset versions. You may need to give yourself execute privileges to run execute this file. In your terminal, run chmod u+x delete_all_datasets_in_a_dataverse.command

token="ENTER_API_TOKEN" # Enter super-user's Dataverse account API token.
server="ENTER_SERVER" # Enter name of server url, which is home page URL of the Dataverse installation, e.g. https://demo.dataverse.org
alias="ENTER_DATAVERSE_ALIAS" # Enter alias of dataverse. E.g. sonias-dataverse.

# This changes the directory to whatever directory this .command file is in, so that deleted_datasetPIDs_in_$alias.txt is saved in that directory.
cd "`dirname "$0"`"

# This uses the Search API and jq to retrieve the persistent IDs (global_id) of datasets in the dataverse. Then it stores the persistent IDs in a text file on the user's computer.
# Change the per_page parameter to retrieve more persistent IDs.
curl "$server/api/search?q=*&subtree=$alias&per_page=50&type=dataset" | jq -r '.data.items[].global_id' > citation_dates_changed_in_$alias.txt

# This loops through the stored persistent IDs and changes the citation dates for those datasets
for global_id in $(cat citation_dates_changed_in_$alias.txt);
do
	# "distributionDate" can be changed to any of Dataverse's date metadata fields
	curl -d "distributionDate" --header "X-Dataverse-key: $token" -X PUT $server/api/datasets/:persistentId/citationdate?persistentId=$global_id

	# Uncomment line below (remove hashtag) to change citation dates back to original citation date (date dataset was first published in the Dataverse repository)
	# curl -X DELETE -H "X-Dataverse-key: $token" $server/api/datasets/:persistentId/citationdate?persistentId=$global_id
done
exit
