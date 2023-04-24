# Move given datasets into a given Dataverse collection

from csv import DictReader
import requests

repositoryURL = ''  # Base URL of the Dataverse repository, e.g. https://demo.dataverse.org
apikey = ''
datasetPIDFile = ''  # Path to .csv or .txt file containing dataset PIDs
alias = '' # Collection to move the datasets into

datasetPIDs = []
if '.csv' in datasetPIDFile:
    with open(datasetPIDFile, mode='r', encoding='utf-8') as f:
        csvDictReader = DictReader(f, delimiter=',')
        for row in csvDictReader:
            datasetPIDs.append(row['persistent_id'].rstrip())

elif '.txt' in datasetPIDFile:
    datasetPIDFile = open(datasetPIDFile)
    for datasetPID in datasetPIDFile:
        datasetPIDs.append(datasetPID.rstrip())

total = len(datasetPIDs)
count = 0

for datasetPID in datasetPIDs:
    url = f'{repositoryURL}/api/datasets/:persistentId/move/{alias}'
    params = {'persistentId': datasetPID}
    req = requests.post(
        url,
        params=params,
        headers={
            'X-Dataverse-key': apikey
        })
    count += 1

    if req.status_code == 200:
        print(f'Success! {count} of {total}: {datasetPID}')
    else:
        print(f'Failure! {count} of {total}: {datasetPID}')
