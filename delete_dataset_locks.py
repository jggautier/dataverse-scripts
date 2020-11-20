# Remove dataset locks

import csv
from csv import DictReader
import requests

repositoryURL = 'https://demo.dataverse.org'
apikey = ''
datasetPIDFile = ''

datasetPIDs = []
if '.csv' in datasetPIDFile:
    reader = csv.reader(open(datasetPIDs))
    total = len(list(reader)) - 1

    with open(datasetPIDFile, mode='r', encoding='utf-8') as f:
        csvDictReader = DictReader(f, delimiter=',')
        for row in csvDictReader:
            datasetPIDs.append(row['persistent_id'].rstrip())

elif '.txt' in datasetPIDFile:
    total = len(open(datasetPIDFile).readlines())
    datasetPIDFile = open(datasetPIDFile)
    for datasetPID in datasetPIDFile:

        # Remove any trailing spaces from datasetPID
        datasetPIDs.append(datasetPID.rstrip())

count = 0
for datasetPID in datasetPIDs:
    url = 'https://demo.dataverse.org/api/datasets/:persistentId/locks?persistentId=%s' % (datasetPID)

    r = requests.delete(
        url,
        headers={
            'X-Dataverse-key': apikey
        })
    count += 1

    if r.status_code == 200:
        print('Success: %s! %s of %s' % (datasetPID, count, total))
    else:
        print('Failed: %s! %s of %s' % (datasetPID, count, total))
