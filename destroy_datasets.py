# Destroys a given list of datasets

from csv import DictReader
import requests

server = 'https://demo.dataverse.org'  # Dataverse repository URL, e.g. https://demo.dataverse.org
apikey = ''  # API key of superuser account
file = ''  # Text or CSV file containing PIDs of datasets to be destroyed, e.g. /Users/user/Desktop/dois.txt

datasetPIDs = []
if '.csv' in file:
    with open(file, mode='r', encoding='utf-8') as f:
        csvDictReader = DictReader(f, delimiter=',')
        for row in csvDictReader:
            datasetPIDs.append(row['persistent_id'].rstrip())

elif '.txt' in file:
    file = open(file)
    for datasetPID in file:

        # Remove any trailing spaces from datasetPID
        datasetPIDs.append(datasetPID.rstrip())

total = len(datasetPIDs)

destroyed_datasets = []
not_destroyed_datasets = []

print('Trying to destroy datasets...')

for datasetPID in datasetPIDs:
    try:
        url = '%s/api/datasets/:persistentId/destroy/?persistentId=%s' % (server, datasetPID)
        headers = {
            'X-Dataverse-key': apikey}

        req = requests.delete(
            url,
            headers={
                'X-Dataverse-key': apikey
            })

        print('%s destroyed' % (datasetPID))
        destroyed_datasets.append(datasetPID)

    except Exception:
        print('Could not destroy %s' % (datasetPID))
        not_destroyed_datasets.append(datasetPID)

print('\nDatasets destroyed: %s' % (len(destroyed_datasets)))
if destroyed_datasets:
    print(destroyed_datasets)

print('\nDatasets not destroyed: %s' % (len(not_destroyed_datasets)))
if not_destroyed_datasets:
    print(not_destroyed_datasets)
