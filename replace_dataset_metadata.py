# Replace dataset metadata in given datasets

from csv import DictReader
import requests

token = ''  # Enter API token of Dataverse account that has edit and publish privileges on the datasets.
server = ''  # Enter name of server url, which is home page URL of the Dataverse installation, e.g. https://demo.dataverse.org

metadatafile = ''  # Path to json file that contains the replacement metadata
datasetPIDs = ''  # File with list of dataset PIDs

with open(datasetPIDs, mode='r', encoding='utf-8') as f:
    total = len(f.readlines()) - 1

count = 0

with open(datasetPIDs, mode='r', encoding='utf-8') as f:
    csv_dict_reader = DictReader(f, delimiter=',')
    for row in csv_dict_reader:
        datasetPID = row['persistent_id'].rstrip()
        url = '%s/api/datasets/:persistentId/editMetadata' % (server)
        r = requests.put(
            url,
            data=open(metadatafile, 'rb'),
            params={
                'persistentId': datasetPID,
                'replace': 'true'
            },
            headers={
                'X-Dataverse-key': token
            })
        count += 1

        if r.status_code == 200:
            print('Success: %s! %s of %s' % (datasetPID, count, total))
        else:
            print('Failed: %s! %s of %s' % (datasetPID, count, total))
