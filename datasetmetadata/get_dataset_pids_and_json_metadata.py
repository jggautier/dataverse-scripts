# Python script for getting the dataset PIDs from a Dataverse repository and downloading the JSON metadata files of those datasets

import json
import os
import requests
from urllib.request import urlopen
from urllib.parse import urlparse
import time
import csv
import pandas as pd

# Ask user for URL of dataverse, e.g. https://demo.dataverse.org/dataverse/demo
dataverse_url = input('\n' + 'Enter full URL of dataverse to add links to:')

# Parse URL to get server name and alias
parsed = urlparse(dataverse_url)
server = parsed.scheme + '://' + parsed.netloc
alias = parsed.path.split('/')[2]

# Create directories

# create parent directory
current_directory = os.path.dirname(os.path.realpath(__file__)) # save directory of this python file
current_time = time.strftime('%Y.%m.%d_%H.%M.%S') # save current time to append it to parent folder name later
parent_directory_path = os.path.join(current_directory, '%s_dataset_metadata_%s' %(alias, current_time))
os.mkdir(parent_directory_path)

# create directory within parent directory for the JSON metadata files
metadata_directory_path = os.path.join(parent_directory_path, 'dataset_metadata')
os.mkdir(metadata_directory_path)
json_directory_path = os.path.join(parent_directory_path, 'dataset_metadata/json')
os.mkdir(json_directory_path)

# Use Search API to get PIDs of datasets in the given dataverse

# Initative counts of terminal progress indicator
rows = 10
start = 0
condition = True

filename = os.path.join(parent_directory_path,'dataset_pids.csv')

print('Copy dataset PIDs to dataset_pids.csv...')

with open(filename, mode = 'w') as metadatafile:
	metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting=csv.QUOTE_MINIMAL)
	metadatafile.writerow(['global_id', 'persistentUrl', 'dataverse']) # Create header row

rows = 10
start = 0
condition = True
query = '*&type=dataset' # query string for search API, e.g. '*&type=dataverse'

while (condition):
	url = server + '/api/search?q=' + query + '&subtree=' + alias + '&start=' + str(start)
	data = json.load(urlopen(url))
	total = data['data']['total_count']
	print('Copied PIDs:', start, 'of total:', total)

	for i in data['data']['items']: # path to object in the Search APIs json
		global_id = i['global_id']
		try:
			dataverse = i['name_of_dataverse']
		except KeyError:
			dataverse = ''

		persistentUrl = i['url']
		with open(filename, mode = 'a') as datasets:
			def to_utf8(lst):
				return [unicode(elem).encode('utf-8') for elem in lst] # Convert all characters to utf-8
			datasets = csv.writer(datasets, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			datasets.writerow([global_id, persistentUrl, dataverse])
	start = start + rows
	condition = start < total
print('Copied PIDs:', start, 'of total:', total)


## ------------------------------------------------------------

# Download JSON metadata from APIs
print('Downloading JSON metadata in dataset_metadata folder...')

# Save csv file as a pandas dataframe
file = pd.read_csv(filename)

# Convert global_id column into a list
dataset_pids = file['global_id'].tolist()

# Initative count for terminal progress indicator
start = 0

# Save number of items in the dataset_pids list in total variable
total = len(dataset_pids)

# For each dataset id in the list, download the dataset's Dataverse JSON file into the metadata folder
for pid in dataset_pids:
	pid = pid.strip()
	url = '%s/api/datasets/export?exporter=dataverse_json&persistentId=%s'%(server, pid)
	r = requests.get(url)
	with open(os.path.join(json_directory_path, 'dataset_%s.json' %(pid.split('/')[-1])), mode = 'w') as f:
		f.write(json.dumps(json.loads(r.content), indent=4, sort_keys=True))
	print('Downloaded %s of %s JSON files' %(start, total))
	start += 1
print('Downloaded %s of %s JSON files' %(total, total))