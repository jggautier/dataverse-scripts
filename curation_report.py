'''
Provide a date range and optional API key and this script will get info for datasets and files created
within that date range. Useful when curating deposited data, especially spotting problem datasets
(e.g. datasets with no data).

This script first uses the Search API to find PIDs of datasets.
For each dataset found, the script uses the "Get JSON" API endpoint to get dataset and file metadata
of the latest version of each dataset, and formats and writes that metadata to a CSV file on the
user's computer. Users can then analyze the CSV file (e.g. grouping, sorting, pivot tables)
for a quick view of what's been published within that date rage, what does and doesn't have files, and more.

This script might break for repositories that are missing certain info from their Search API JSON
results, like the datasetPersistentId key (data/latestVersion/datasetPersistentId)
'''

import csv
from datetime import datetime
from dateutil import tz
from functools import reduce
import json
import os
import pandas as pd
import requests
from requests.exceptions import HTTPError
import sys

# Get required info from user
server = ''  # Base URL of the Dataverse repository, e.g. https://demo.dataverse.org
startDate = ''  # yyyy-mm-dd
endDate = ''  # yyyy-mm-dd
apiKey = ''  # for getting unpublished datasets accessible to Dataverse account
directory = ''  # directory for CSV file containing dataset and file info, e.g. '/Users/username/Desktop/'
ignoreCollections = []  # alias of collections whose datasets should be ignored


# Function for converting given timestamp string with UTC timezone into datetime object with local timezone
def convert_to_local_tz(timestamp):
    # Save local timezone to localTimezone variable
    localTimezone = tz.tzlocal()
    # Convert string to datetime object
    timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
    # Convert from UTC to local timezone
    timestamp = timestamp.astimezone(localTimezone)
    return timestamp


# Function for converting bytes to more human-readable KB, MB, etc
def format_bytes(size):
    power = 2**10
    n = 0
    powerLabels = {0: 'bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return '%s %s' % (round(size, 2), powerLabels[n])


start = 0

# Get total count of datasets
searchApiUrl = '%s/api/search' % (server)
dateSort = 'dateSort:[%sT00:00:00Z TO %sT23:59:59Z]' % (startDate, endDate)
perPage = 1
params = {
    'q': '*',
    'fq': {'-metadataSource:"Harvested"', dateSort},
    'type': 'dataset',
    'per_page': perPage,
    'start': start
}
response = requests.get(
    searchApiUrl,
    params=params,
    headers={'X-Dataverse-key': apiKey}
)
data = response.json()

# If Search API is working, get total
if data['status'] == 'OK':
    total = data['data']['total_count']

# If Search API is not working, print error message and stop script
elif data['status'] == 'ERROR':
    errorMessage = data['message']
    print(errorMessage)
    exit()

# # If user enters any collections in ignoreCollections list, get alias of any collections within those collections

# if ignoreCollections:
#     ignoreTotal = 0
#     dataverseAliases = []

#     # Get database IDs of collections entered and any collections within them
#     for collection in ignoreCollections:
#         params['subtree'] = collection
#         response = requests.get(
#             searchApiUrl,
#             params=params,
#             headers={'X-Dataverse-key': apiKey}
#         )
#         data = response.json()
#         ignoreTotal = data['data']['total_count'] + ignoreTotal

#     total = total - ignoreTotal
#     params.pop('subtree', None)

misindexedDatasetsCount = 0
datasetInfoDict = []

# Initialization for paginating through results of Search API calls
condition = True

print('Searching for dataset PIDs:')
while condition:
    try:
        params['per_page'] = 10
        response = requests.get(
            searchApiUrl,
            params=params,
            headers={'X-Dataverse-key': apiKey}
        )
        data = response.json()

        for i in data['data']['items']:
            if i['versionState'] != 'DEACCESSIONED':
                dataverseNameAlias = '%s (%s)' % (i['name_of_dataverse'], i['identifier_of_dataverse'])
                newRow = {
                    'datasetPID': i['global_id'],
                    'dataverseNameAlias': dataverseNameAlias,
                    'dataverseAlias': i['identifier_of_dataverse']}
                datasetInfoDict.append(dict(newRow))

        print('Dataset PIDs found: %s of %s' % (len(datasetInfoDict), total))

        # Update variables to paginate through the search results
        params['start'] = params['start'] + params['per_page']

    # If misindexed datasets break the Search API call where per_page=10,
    # try calls where per_page=1 then per_page=10 again
    # (See https://github.com/IQSS/dataverse/issues/4225)
    except Exception:
        try:
            params['per_page'] = 1
            response = requests.get(
                searchApiUrl,
                params=params,
                headers={'X-Dataverse-key': apiKey}
            )
            data = response.json()

            for i in data['data']['items']:
                if i['versionState'] != 'DEACCESSIONED':
                    dataverse = '%s (%s)' % (i['identifier_of_dataverse'], i['name_of_dataverse'])
                    newRow = {
                        'datasetPID': i['global_id'],
                        'dataverseNameAlias': dataverseNameAlias,
                        'dataverseAlias': i['identifier_of_dataverse']}
                    datasetInfoDict.append(dict(newRow))

            print('Dataset PIDs found: %s of %s' % (len(datasetInfoDict), total))

            # Update variables to paginate through the search results
            params['start'] = params['start'] + params['per_page']

        # If page fails to load, count a misindexed dataset and continue to the next page
        except Exception:
            misindexedDatasetsCount += 1
            params['start'] = params['start'] + params['per_page']

    condition = params['start'] < total

datasetDataverseInfoDF = pd.DataFrame(datasetInfoDict)

# If there are duplicate PIDs, report the number of unique PIDs and explain:
# Where there are published datasets with a draft version, the Search API lists the PID twice,
# once for published versions and once for draft versions.
datasetDataverseInfoDF = datasetDataverseInfoDF.drop_duplicates()
if total != len(datasetDataverseInfoDF):
    total = len(datasetDataverseInfoDF)
    print('Unique datasets: %s\n\tThe Search API returns both the draft and most \
recently published versions of datasets.\n\tAny deaccessioned datasets have been skipped.' % (total))

# Remove any rows in datasetDataverseInfoDF whose dataverseAlias column contains
# any values in the ignoreCollections list. Then drop dataverseAlias column
if ignoreCollections:
    print('\nRemoving datasets from collections you would like to ignore...')
    datasetDataverseInfoDF = datasetDataverseInfoDF[~datasetDataverseInfoDF['dataverseAlias'].isin(ignoreCollections)]
    datasetDataverseInfoDF = datasetDataverseInfoDF.drop(columns=['dataverseAlias'])
    total = len(datasetDataverseInfoDF)
    print('Count of datasets excluding datasets in ignored collections: %s' % (total))

# For each data file in each dataset, add to a dictionary the dataset's URL and
# publication state, dataset title, data file name and data file contentType

print('\nGetting dataset and file info:')

# Create list to store any PIDs whose info can't be retrieved with "Get JSON" or Search API endpoints
pidErrors = []
datafileInfoDict = []

count = 0
for datasetPID in datasetDataverseInfoDF['datasetPID']:
    count += 1
    print('Getting metadata for %s: %s of %s' % (datasetPID, count, total))
    # Construct "Get JSON" API endpoint url and get data about each dataset's latest version
    try:
        dataGetLatestVersionUrl = '%s/api/datasets/:persistentId' % (server)
        response = requests.get(
            dataGetLatestVersionUrl,
            params={'persistentId': datasetPID},
            headers={'X-Dataverse-key': apiKey}
        )

        # Store dataset and file info from API call to "dataGetLatestVersion" variable
        dataGetLatestVersion = response.json()

    except Exception:
        pidErrors.append(datasetPID)

    # Check for "latestVersion" key. Deaccessioned datasets have no "latestVersion" key.
    if 'latestVersion' in dataGetLatestVersion['data']:

        # Save dataset info
        dsTitle = dataGetLatestVersion['data']['latestVersion']['metadataBlocks']['citation']['fields'][0]['value']
        datasetPersistentId = dataGetLatestVersion['data']['latestVersion']['datasetPersistentId']
        if 'publicationDate' not in dataGetLatestVersion['data']:
            versionState = 'UNPUBLISHED'
        else:
            versionState = 'PUBLISHED' + '/' + dataGetLatestVersion['data']['latestVersion']['versionState']
        datasetInfo = '%s (%s) (%s)' % (dsTitle, versionState, datasetPersistentId)

        # Get date of latest dataset version
        lastUpdateTime = convert_to_local_tz(dataGetLatestVersion['data']['latestVersion']['lastUpdateTime'])

        # If the dataset's latest version contains files, write dataset and file info (file name,
        # file type, and size) to the CSV
        if dataGetLatestVersion['data']['latestVersion']['files']:
            for datafile in dataGetLatestVersion['data']['latestVersion']['files']:
                datafileName = datafile['label']
                datafileSize = format_bytes(datafile['dataFile']['filesize'])
                datafileType = datafile['dataFile']['contentType']
                datafileNameSize = '%s (%s)' % (datafileName, datafileSize)

                # Add fields to a new row in datafileInfoDict
                newRow = {
                    'datasetPID': datasetPersistentId,
                    'datasetInfo': datasetInfo,
                    'datafileNameSize': datafileNameSize,
                    'datafileType': datafileType,
                    'lastUpdateTime': lastUpdateTime
                }
                datafileInfoDict.append(dict(newRow))

        # Otherwise add row in datafileInfoDict that the dataset has no files
        else:
            newRow = {
                'datasetPID': datasetPersistentId,
                'datasetInfo': datasetInfo,
                'datafileNameSize': '(no files found)',
                'datafileType': '(no files found)',
                'lastUpdateTime': lastUpdateTime
            }
            datafileInfoDict.append(dict(newRow))

print('Finished getting dataset and file info of %s dataset(s)' % (total))

# If info of any PIDs could not be retrieved, print list of those PIDs
if pidErrors:

    # Deduplicate list in pidErrors variable
    pidErrors = set(pidErrors)

    print('Info about the following PIDs could not be retrieved. To investigate, \
try running "Get JSON" endpoint or Search API on these datasets:')
    print(*pidErrors, sep='\n')

datafileInfoDF = pd.DataFrame(datafileInfoDict)


# Join datafileInfoDF and datasetDataverseInfoDF on the datasetPID column
dataframes = [datafileInfoDF, datasetDataverseInfoDF]

# For each dataframe, set the indexes (or the common columns across the dataframes to join on)
for dataframe in dataframes:
    dataframe.set_index(['datasetPID'], inplace=True)

print('\nPreparing report...')

# Merge all dataframes and save to the 'merged' variable
report = reduce(lambda left, right: left.join(right, how='outer'), dataframes).reset_index()

report = report.drop(columns=['datasetPID'])

fileName = 'datasetinfo_%s-%s.csv' % (startDate.replace('-', '.'), endDate.replace('-', '.'))
csvFilePath = os.path.join(directory, fileName)

report.to_csv(csvFilePath, index=False)
print('Report saved to %s' % (csvFilePath))
