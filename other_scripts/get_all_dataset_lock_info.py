import csv
from dateutil import tz
from dateutil.parser import parse
import json
import requests
import time


def convert_to_local_tz(timestamp, shortDate=False):
    # Save local timezone to localTimezone variable
    localTimezone = tz.tzlocal()
    # Convert string to datetime object
    timestamp = parse(timestamp)
    # Convert timestamp to local timezone
    timestamp = timestamp.astimezone(localTimezone)
    if shortDate is True:
        # Return timestamp in YYYY-MM-DD format
        timestamp = timestamp.strftime('%Y-%m-%d')
    return timestamp


# Get apiToken and directory to save CSV file from user
apiToken = ''
directoryPath = ''

installationUrl = 'https://dataverse.harvard.edu'

# List lock types. See https://guides.dataverse.org/en/5.10/api/native-api.html?highlight=locks#list-locks-across-all-datasets
lockTypesList = ['Ingest', 'finalizePublication']

# Create csvFilePath
currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')
fileName = 'datasetlocks_%s.csv' %(currentTime)
csvFilePath = '%s/%s' %(directoryPath, fileName)

# Create CSV file and header row
headerRow = ['dataset_pid', 'dataset_url', 'lock_type', 'lock_date', 'user', 'message']
with open(csvFilePath, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(headerRow)

# Add dataset lock info to CSV file
with open(csvFilePath, mode='a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for lockType in lockTypesList:

        datasetLocksApiEndpoint = '%s/api/datasets/locks?type=%s' % (installationUrl, lockType)
        req = requests.get(
            datasetLocksApiEndpoint,
            headers={'X-Dataverse-key': apiToken})
        data = req.json()
        if data['status'] == 'OK':
            for lock in data['data']:
                datasetPid = lock['dataset']
                datasetUrl = 'https://dataverse.harvard.edu/dataset.xhtml?persistentId=%s' % (datasetPid)
                lockType = lock['lockType']
                date = convert_to_local_tz(lock['date'], shortDate=True)
                user = lock['user']
                message = lock['message']

                writer.writerow([datasetPid, datasetUrl, lockType, date, user, message]) 
            


