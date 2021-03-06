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
import json
import os
import requests
from requests.exceptions import HTTPError
import sys

# Get required info from user
server = ''  # Base URL of the Dataverse repository, e.g. https://demo.dataverse.org
startDate = ''  # yyyy-mm-dd
endDate = ''  # yyyy-mm-dd
apiKey = ''  # for getting unpublished datasets accessible to Dataverse account
directory = ''  # directory for CSV file containing dataset and file info, e.g. '/Users/username/Desktop/'

# List for storing indexed dataset PIDs and variable for counting misindexed datasets
datasetPids = []
misindexedDatasetsCount = 0

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

        # For each dataset...
        for i in data['data']['items']:

            # Get the dataset PID and add it to the datasetPids list
            globalId = i['global_id']
            datasetPids.append(globalId)

        print('Dataset PIDs found: %s of %s' % (len(datasetPids), total), end='\r', flush=True)

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

            # Get dataset PID and save to datasetPids list
            globalId = data['data']['items'][0]['global_id']
            datasetPids.append(globalId)

            print('Dataset PIDs found: %s of %s' % (len(datasetPids), total), end='\r', flush=True)

            # Update variables to paginate through the search results
            params['start'] = params['start'] + params['per_page']

        # If page fails to load, count a misindexed dataset and continue to the next page
        except Exception:
            misindexedDatasetsCount += 1
            params['start'] = params['start'] + params['per_page']

    # Stop paginating when there are no more results
    condition = params['start'] < total

if misindexedDatasetsCount:
    print('\n\nDatasets misindexed: %s\n' % (misindexedDatasetsCount))

# If there are duplicate PIDs, report the number of unique PIDs and explain:
# Where there are published datasets with a draft version, the Search API lists the PID twice,
# once for published versions and once for draft versions.
if len(datasetPids) != len(set(datasetPids)):
    uniqueDatasetPids = set(datasetPids)
    print('Unique datasets: %s (The Search API returns both the draft and most \
recently published versions of datasets)' % (len(uniqueDatasetPids)))

# Otherwise, copy datasetPids to uniqueDatasetPids variable
else:
    uniqueDatasetPids = datasetPids

# Store name of CSV file, which includes the dataset start and end date range, to the 'filename' variable
fileName = 'datasetinfo_%s-%s.csv' % (startDate.replace('-', '.'), endDate.replace('-', '.'))

# Create variable for directory path and file name
csvFilePath = os.path.join(directory, fileName)


# Convert given timestamp string with UTC timezone into datetime object with local timezone
def convert_to_local_tz(timestamp):
    # Save local timezone to localTimezone variable
    localTimezone = tz.tzlocal()
    # Convert string to datetime object
    timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
    # Convert from UTC to local timezone
    timestamp = timestamp.astimezone(localTimezone)
    return timestamp


# Create CSV file
with open(csvFilePath, mode='w') as openCsvFile:
    openCsvFile = csv.writer(openCsvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Create header row
    openCsvFile.writerow([
        'datasetTitle (versionState) (DOI)', 'fileName (fileSize)',
        'fileType', 'lastUpdateTime', 'dataverseName (alias)'])

# For each data file in each dataset, add to the CSV file the dataset's URL and
# publication state, dataset title, data file name and data file contentType

print('\nWriting dataset and file info to %s:' % (csvFilePath))

# Create list to store any PIDs whose info can't be retrieved with "Get JSON" or Search API endpoints
pidErrors = []


# Function for converting bytes to more human-readable KB, MB, etc
def format_bytes(size):
    power = 2**10
    n = 0
    powerLabels = {0: 'bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return '%s %s' % (round(size, 2), powerLabels[n])


count = 0
for pid in uniqueDatasetPids:
    count += 1
    print('Getting metadata for %s: %s of %s' % (pid, count, len(uniqueDatasetPids)))
    # Construct "Get JSON" API endpoint url and get data about each dataset's latest version
    try:
        dataGetLatestVersionUrl = '%s/api/datasets/:persistentId' % (server)
        response = requests.get(
            dataGetLatestVersionUrl,
            params={'persistentId': pid},
            headers={'X-Dataverse-key': apiKey}
        )

        # Store dataset and file info from API call to "dataGetLatestVersion" variable
        dataGetLatestVersion = response.json()

    except Exception:
        pidErrors.append(pid)

    # Check for "latestVersion" key. Deaccessioned datasets have no "latestVersion" key.
    if 'latestVersion' in dataGetLatestVersion['data']:

        # Construct "Search API" url to get name of each dataset's dataverse
        try:
            q = '"%s"' % (pid)
            response = requests.get(
                searchApiUrl,
                params={'q': q, 'type': 'dataset'},
                headers={'X-Dataverse-key': apiKey}
            )

            dataDataverseName = response.json()
        except Exception:
            pidErrors.append(pid)

        # Save dataverse name and alias
        dataverseName = dataDataverseName['data']['items'][0]['name_of_dataverse']
        dataverseAlias = dataDataverseName['data']['items'][0]['identifier_of_dataverse']
        dataverseNameAlias = '%s (%s)' % (dataverseName, dataverseAlias)

        # Save dataset info
        dsTitle = dataGetLatestVersion['data']['latestVersion']['metadataBlocks']['citation']['fields'][0]['value']
        datasetPersistentId = dataGetLatestVersion['data']['latestVersion']['datasetPersistentId']
        versionState = dataGetLatestVersion['data']['latestVersion']['versionState']
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
                datafileInfo = '%s (%s)' % (datafileName, datafileSize)

                # Add fields to a new row in the CSV file
                with open(csvFilePath, mode='a', encoding='utf-8') as openCsvFile:

                    openCsvFile = csv.writer(openCsvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                    # Create new row with dataset and file info
                    openCsvFile.writerow([datasetInfo, datafileInfo, datafileType, lastUpdateTime, dataverseNameAlias])

                    # As a progress indicator, print a dot each time a row is written
                    # sys.stdout.write('.')
                    # sys.stdout.flush()

        # Otherwise write to the CSV that the dataset has no files
        else:
            with open(csvFilePath, mode='a') as openCsvFile:

                openCsvFile = csv.writer(
                    openCsvFile, delimiter=',', quotechar='"',
                    quoting=csv.QUOTE_MINIMAL)

                # Create new row with dataset and file info
                openCsvFile.writerow([
                    datasetInfo, '(no files found)', '(no files found)',
                    lastUpdateTime, dataverseNameAlias])

                # As a progress indicator, print a dot each time a row is written
                # sys.stdout.write('.')
                # sys.stdout.flush()

print('\nFinished writing dataset and file info of %s dataset(s) to %s' % (len(uniqueDatasetPids), csvFilePath))

# If info of any PIDs could not be retrieved, print list of those PIDs
if pidErrors:

    # Deduplicate list in pidErrors variable
    pidErrors = set(pidErrors)

    print('Info about the following PIDs could not be retrieved. To investigate, \
try running "Get JSON" endpoint or Search API on these datasets:')
    print(*pidErrors, sep='\n')
