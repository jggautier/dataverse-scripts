# For non-harvested datasets created within a range of time, get dataset and file info. Useful for spotting problem datasets (e.g. dataset with no data)
# This script first uses the Search API to find PIDs of datasets.
# For each dataset found, the script uses the "get versions" API endpoint to get dataset and file metadata.
# The script formats and writes that metadata to a CSV file on the users computer

import csv
import json
import os
import sys
import urllib.request
from urllib.request import urlopen

# Get required info from user
server='https://dataverse.harvard.edu' # Dataverse repository must have Search API and "get version" endpoints unblocked
startdate='' # yyyy-mm-dd
enddate='' # yyyy-mm-dd
apikey='' # for getting unpublished datasets accessible to Dataverse account
directory='' # directory for the CSV file containing the dataset and file info, e.g. '/Users/username/Desktop/'

# Initialization for paginating through Search API results
rows=10
start=0
page = 1
count=0
condition=True

# List for storing dataset PIDs
dataset_pids=[]

print('Getting dataset PIDs:')

while (condition):
	try:
		url='%s/api/search?q=*&fq=metadataSource:"Harvard+Dataverse"&type=dataset&per_page=10&start=%s&sort=date&order=desc&fq=dateSort:[%sT00:00:00Z+TO+%sT23:59:59Z]&key=%s' %(server, start, startdate, enddate, apikey)
		data=json.load(urlopen(url))

		# Get total number of results
		total=data['data']['total_count']

		# For each item object...
		for i in data['data']['items']:

			# Get the dataset PID and add it to the dataset_pids list
			global_id=i['global_id']
			dataset_pids.append(global_id)

		# Update variables to paginate through the search results
		start=start + rows
		page+=1
		count+=10

		# Stop paginating when there are no more results
		condition=start < total

		# As a progress indicator, print a dot for each page
		sys.stdout.write('.')
		sys.stdout.flush()

	# Print error message if misindexed datasets break the Search API call, and try the next page. (See https://github.com/IQSS/dataverse/issues/4225)
	except urllib.error.URLError:
		print('\nCould not get %s datasets. A dataset indexing error is preventing the following URL from loading:\n%s\n' %(rows, url))
		start=start + rows
		page+=1

print('\nFound %s of %s datasets' %(len(dataset_pids), total))

# Store name of csv file, which includes the dataset start and end date range, to the 'filename' variable
filename='datasetinfo_%s-%s.csv' %(startdate.replace('-', '.'), enddate.replace('-', '.'))

# Create variable for directory path and file name
csvfile=os.path.join(directory, filename)

# Create CSV file
with open(csvfile, mode='w') as writecsvfile:
	writecsvfile=csv.writer(writecsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	
	# Create header row
	writecsvfile.writerow(['datasetURL (publication state)', 'ds_title', 'fileinfo'])

# For each data file in each dataset, add to the CSV file the dataset's URL and publication state, dataset title, data file name and data file contentType

print('\nWriting dataset and file info to %s:' %(csvfile))

count=0

for pid in dataset_pids:
	# Construct "Get Versions" API url
	url='https://dataverse.harvard.edu/api/datasets/:persistentId/versions/?persistentId=%s&key=%s' %(pid, apikey)
	
	# Store dataset and file info from API call to "data" variable
	data=json.load(urlopen(url))

	# Save dataset title, URL and publication state
	ds_title=data['data'][0]['metadataBlocks']['citation']['fields'][0]['value']
	datasetPersistentId=data['data'][0]['datasetPersistentId']
	datasetURL='https://dataverse.harvard.edu/dataset.xhtml?persistentId=%s' %(datasetPersistentId)
	versionState=data['data'][0]['versionState']
	datasetURL_pubstate='%s (%s)' %(datasetURL, versionState)

	# If the dataset contains files, write dataset and file info (file name, size and contenttype) to the CSV
	if data['data'][0]['files']:
		for file in data['data'][0]['files']:
			filename=file['label']
			filesize=file['dataFile']['filesize']
			contentType=file['dataFile']['contentType']
			fileinfo='%s (%s bytes; %s)' %(filename, filesize, contentType)

			# Append fields to the csv file
			with open(csvfile, mode='a') as writecsvfile:
		
				# Convert all characters to utf-8
				def to_utf8(lst):
					return [unicode(elem).encode('utf-8') for elem in lst]

				writecsvfile=csv.writer(writecsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
				
				# Create new row with dataset and file info
				writecsvfile.writerow([datasetURL_pubstate, ds_title, fileinfo])

				# As a progress indicator, print a dot each time a row is written
				sys.stdout.write('.')
				sys.stdout.flush()

	# Otherwise print that the dataset has no files
	else:
		with open(csvfile, mode='a') as writecsvfile:
		
			# Convert all characters to utf-8
			def to_utf8(lst):
				return [unicode(elem).encode('utf-8') for elem in lst]

			writecsvfile=csv.writer(writecsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			
			# Create new row with dataset and file info
			writecsvfile.writerow([datasetURL_pubstate, ds_title, '(no files found)'])

			# As a progress indicator, print a dot each time a row is written
			sys.stdout.write('.')
			sys.stdout.flush()
print('\n')
