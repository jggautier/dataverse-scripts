# Replace dataset metadata in given datasets

from csv import DictReader
import requests

server = 'https://demo.dataverse.org/'  # Enter name of server url, which is home page URL of the Dataverse installation, e.g. https://demo.dataverse.org
token = ''  # Enter API token of Dataverse account that has edit privileges on the datasets

metadatafile = ''  # Path to JSON file that contains the replacement metadata
datasetPIDs = ''  # Path to CSV file with list of dataset PIDs

with open(datasetPIDs, mode='r', encoding='utf-8') as f:
    total = len(f.readlines()) - 1

count = 0

with open(datasetPIDs, mode='r', encoding='utf-8') as f:
    csv_dict_reader = DictReader(f, delimiter=',')
    for row in csv_dict_reader:
        # title = 'dataset %s' % (str(count))
        title = row['title'].rstrip()
        metadataValues = {
            "fields": [
                {
                    "typeName": "title",
                    "value": title
                }
            ]
        }

        datasetPID = row['persistent_id'].rstrip()
        url = '%s/api/datasets/:persistentId/editMetadata' % (server)
        params = {'persistentId': datasetPID, 'replace': 'true'}
        r = requests.put(
            url,
            # data=open(metadatafile, 'rb'),
            json=metadataValues,
            params=params,
            headers={
                'X-Dataverse-key': token,
                'content-type': 'application/json'
            })
        count += 1

        if r.status_code == 200:
            print('Success: %s! %s of %s' % (datasetPID, count, total))
        else:
            print('Failed: %s! %s of %s' % (datasetPID, count, total))
