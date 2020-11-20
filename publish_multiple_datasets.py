# Publish a given list of datasets

import csv
from csv import DictReader
import requests

repositoryURL = 'https://demo.dataverse.org'
apikey = ''
datasetPIDFile = ''
type = ''

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
    url = '%s/api/datasets/:persistentId/actions/:publish' % (repositoryURL)
    params = {'persistentId': datasetPID, 'type': type}
    r = requests.post(
        url,
        params=params,
        headers={
            'X-Dataverse-key': apikey
        })
    count += 1

    if r.status_code == 200:
        print('Success: %s! %s of %s' % (datasetPID, count, total))
    else:
        print('Failed: %s! %s of %s' % (datasetPID, count, total))
