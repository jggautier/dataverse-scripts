#!/bin/bash

# Script for publishing the draft versions of unpublished datasets in a given dataverse. After making edits to this .command file, double click it to run it.
# Mac OS bias: The script has been tested only on Mac OS and instructions may not be helpful for use in other operating systems.
# Software dependencies: You'll need to download jq (https://stedolan.github.io/jq) to run the part of the script that uses the Search API.
# Getting this .command file to work: You may need to give yourself execute privileges to execute this file. In your Mac terminal, run chmod u+x replace_dataset_metadata_in_a_dataverse.command


token="ENTER_API_TOKEN" # Enter API token of Dataverse account that has edit and publish privileges on the datasets.
server="ENTER_SERVER" # Enter name of server url, which is the home page URL of the Dataverse installation, e.g. https://demo.dataverse.org
# alias="ENTER_DATAVERSE_ALIAS" # Enter alias of dataverse. E.g. sonias-dataverse would be the alias of a dataverse with the URL https://demo.dataverse.org/dataverse/sonias-dataverse
datasets="ENTER_FILE_NAME.TXT" # Enter name and extension of file that lists the dataset DOIs.

# This changes the directory to whatever directory this .command file is in, so that the script knows where to find the text file containing the dataset DOIs.
cd "`dirname "$0"`"

# This uses Dataverse's Search API and jq to retrieve the persistent IDs (global_id) of queried datasets in the dataverse. Then it stores the persistent IDs in a text file on the your computer.
# Change the per_page parameter (i.e. per_page=50) to retrieve more persistent IDs, up to 1000 PIDs.
#curl "$server/api/search?q=*&subtree=$alias&per_page=50&type=dataset" | jq -r --arg alias "$alias" '.data.items | map(select(.identifier_of_dataverse==$alias))[].global_id' > $datasets

# This loops through the persistent IDs (global_id) stored in the text file, removes any carriage return characters at the ends of those IDs, and publishes the draft dataset versions.
for global_id in $(cat $datasets);
do
	global_id=${global_id%$'\r'} # If any global_ids in the text file end with carriage returns, which would break the url, this removes those carriage returns.
	curl -H X-Dataverse-key:$token -X POST "$server/api/datasets/:persistentId/actions/:publish?persistentId=$global_id&type=major"
done

exit
