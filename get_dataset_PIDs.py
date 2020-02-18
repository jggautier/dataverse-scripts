# For a given dataverse, get its sub-dataverses or datasets. Includes deaccessioned datasets. Excludes harvested and linked datasets.

import glob
import os
import csv
import json
import os
import sys
import time
import urllib.request
from urllib.request import urlopen
from urllib.parse import urlparse

####################################################################################
# Get IDs of dataverses within the given dataverse and save as a list with parent dataverse - excludes linked dataverses

server=''
alias=''

# To get unpublished dataverses and datasets, user needs to provide api key of an authoritized Dataverse account
apikey=''
# apikey=''

get_subdataverses='' # Enter 'yes' or 'no'

# Get ID of given dataverse alias
if apikey:
	url='%s/api/dataverses/%s?key=%s' %(server, alias, apikey)
else:
	url='%s/api/dataverses/%s' %(server, alias)

data=json.load(urlopen(url))
dataverse_id=data['data']['id']

# Create list and add ID of given dataverse
dataverse_ids=[dataverse_id]


# If user wants datasets in subdataverses, search for and include IDs of subdataverses

# Get each sub-dataverse in the given dataverse
if get_subdataverses=='yes': # If user indicates that she wants subdataverses...
	print('Getting dataverse IDs in %s:' %(alias))
	count=1

	for dataverse_id in dataverse_ids:
		# As a progress indicator, print a dot each time a row is written
		sys.stdout.write('.')
		sys.stdout.flush()
		if apikey:
			url='%s/api/dataverses/%s/contents?key=%s' %(server, dataverse_id, apikey)
		else:
			url='%s/api/dataverses/%s/contents' %(server, dataverse_id)
		data=json.load(urlopen(url))
		for i in data['data']:
			if i['type']=='dataverse':
				dataverse_id=i['id']
				dataverse_ids.extend([dataverse_id])
				count+=1
	print('\n%s dataverse IDs saved' %(len(dataverse_ids)))

####################################################################################
# For each dataverse in the list, get the PIDs of all datasets - excludes linked and harvested datasets

print('Getting dataset IDs:')

count=0
for id in dataverse_ids:
	if apikey:
		url='%s/api/dataverses/%s/contents?key=%s' %(server, id, apikey)
	else:
		url='%s/api/dataverses/%s/contents' %(server, id)
	data=json.load(urlopen(url))

	for i in data['data']:
		if i['type']=='dataset':
			protocol=i['protocol']
			authority=i['authority']
			identifier=i['identifier']
			print('%s:%s/%s' %(protocol, authority, identifier))

			# As a progress indicator, print a dot each time a row is written
			# sys.stdout.write('.')
			# sys.stdout.flush()

			count+=1

print('Datasets saved: %s' %(count))