# Get info about any locks on datasets

import csv
from csv import DictReader
from datetime import datetime
from dateutil import tz
import os
import requests
import time

repositoryURL = ''
inputFile = ''  # Path to .txt or .csv file with database IDs of dataverses to be deleted
directory = '' # Path to directory where CSV file containing lock info will be created


# Function for converting given timestamp string into datetime object with local timezone
def convert_to_local_tz(timestamp):
    # Save local timezone to localTimezone variable
    localTimezone = tz.tzlocal()
    # Convert string to datetime object
    timestamp = datetime.strptime(timestamp, '%a %b %d %H:%M:%S %Z %Y')
    # Convert from UTC to local timezone
    timestamp = timestamp.astimezone(localTimezone)
    return timestamp


current_time = time.strftime('%Y.%m.%d_%H.%M.%S')

datasetPIDs = []
if '.csv' in inputFile:
    with open(inputFile, mode='r', encoding='utf-8') as f:
        csvDictReader = DictReader(f, delimiter=',')
        for row in csvDictReader:
            datasetPIDs.append(row['persistent_id'].rstrip())

elif '.txt' in inputFile:
    inputFile = open(inputFile)
    for datasetPID in inputFile:

        # Remove any trailing spaces from datasetPID
        datasetPIDs.append(datasetPID.rstrip())

total = len(datasetPIDs)
count = 0

# Create CSV file
csvOutputFile = 'dataset_locked_status_%s.csv' % (current_time)
csvOutputFilePath = os.path.join(directory, csvOutputFile)

with open(csvOutputFilePath, mode='w', newline='') as f:
    f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    f.writerow(['persistent_id', 'locked', 'reason', 'locked_date', 'user_name'])

    for datasetPID in datasetPIDs:
        url = '%s/api/datasets/:persistentId/locks?persistentId=%s' % (repositoryURL, datasetPID)
        req = requests.get(url)
        data = req.json()

        count += 1

        if len(data['data']) > 0:
            for lock in data['data']:
                locked = True
                reason = lock['lockType']
                lockedDate = convert_to_local_tz(lock['date'])
                userName = lock['user']
                f.writerow([datasetPID, locked, reason, lockedDate, userName])

            print('%s of %s datasets: %s' % (count, total, datasetPID))
        else:
            locked = False
            reason = 'NA (Not locked)'
            lockedDate = ''
            userName = 'NA (Not locked)'
            f.writerow([datasetPID, locked, reason, lockedDate, userName])

            print('%s of %s datasets: %s' % (count, total, datasetPID))
