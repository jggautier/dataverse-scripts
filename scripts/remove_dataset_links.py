# Removes datasets linked in a dataverse collection

from csv import DictReader
import requests

server = 'https://demo.dataverse.org'  # Dataverse repository URL, e.g. https://demo.dataverse.org
apikey = ''  # API key of superuser account
file = ''  # Text or CSV file containing PIDs of datasets linked in a dataverse collection, e.g. /Users/user/Desktop/dois.txt
dataverseAlias = ''  # Alias of dataverse containing linked datasets to be removed

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

removed_links = []
not_removed_links = []

print('Trying to remove dataset links...')

for datasetPID in datasetPIDs:
    try:
        url = '%s/api/datasets/:persistentId/deleteLink/%s/?persistentId=%s' % (server, dataverseAlias, datasetPID)
        headers = {
            'X-Dataverse-key': apikey}

        req = requests.delete(
            url,
            headers={
                'X-Dataverse-key': apikey
            })

        print('%s destroyed' % (datasetPID))
        removed_links.append(datasetPID)

    except Exception:
        print('Could not remove link to %s' % (datasetPID))
        not_removed_links.append(datasetPID)

print('\nLinks removed: %s' % (len(removed_links)))
if removed_links:
    print(removed_links)

print('\nLinks not removed: %s' % (len(not_removed_links)))
if not_removed_links:
    print(not_removed_links)
