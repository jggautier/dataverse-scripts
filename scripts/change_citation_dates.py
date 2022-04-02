'''
For a given list of datasets, changes the date used in the dataset citation from the default
(date when datasets were first published in the Dataverse repository) to the date in another date
metadata field, e.g. distributionDate
'''

from csv import DictReader
import requests

server = ''  # Dataverse repository URL, e.g. https://demo.dataverse.org
apikey = ''  # API key of super user account
file = ''  # Text file containing PIDs of datasets whose citation dates should be changed
data = b'distributionDate'  # Provide database name of date metadata field to use for citation date

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

citation_dates_changed = []
citation_dates_not_changed = []

print('Trying to change citation dates...')

for datasetPID in datasetPIDs:
    datasetPID = datasetPID.rstrip()
    url = '%s/api/datasets/:persistentId/citationdate?persistentId=%s' % (server, datasetPID)

    try:
        req = requests.put(
            url,
            data=data,
            headers={
                'X-Dataverse-key': apikey
            })

        print('%s: citation date changed' % (datasetPID))
        citation_dates_changed.append(datasetPID)

    except Exception:
        print('%s: Could not change citation date' % (datasetPID))
        citation_dates_not_changed.append(datasetPID)

print('\nDataset citation dates changed: %s' % (len(citation_dates_changed)))
if citation_dates_changed:
    print(citation_dates_changed)

if citation_dates_not_changed:
    print('\nDataset citation dates not changed: %s' % (len(citation_dates_not_changed)))
    print(citation_dates_not_changed)
