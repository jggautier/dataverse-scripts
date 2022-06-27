# Remove dataset locks

from csv import DictReader
import requests

repositoryURL = ''
apikey = ''  # API key of superuser account
file = ''  # Path to .txt or .csv file with database IDs of dataverses to be deleted

datasetPIDs = []

if '.csv' in file:
    with open(file, mode='r', encoding='utf-8') as f:
        csvDictReader = DictReader(f, delimiter=',')
        for row in csvDictReader:
            datasetPIDs.append(row['dataset_pid'].rstrip())

elif '.txt' in file:
    file = open(file)
    for datasetPID in file:

        # Remove any trailing spaces from datasetPID
        datasetPIDs.append(datasetPID.rstrip())

total = len(datasetPIDs)
count = 0

for datasetPID in datasetPIDs:
    url = f'{repositoryURL}/api/datasets/:persistentId/locks?persistentId={datasetPID}'
    req = requests.delete(
        url,
        headers={
            'X-Dataverse-key': apikey
        })

    count += 1

    if req.status_code == 200:
        print(f'Success!: {datasetPID} {count} of {total}')
    else:
        print(f'Failure: {datasetPID} {count} of {total}')
