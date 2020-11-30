# Destroys a given list of datasets

from csv import DictReader
import urllib.request

# Dataverse repository URL, e.g. https://demo.dataverse.org
server = 'https://demo.dataverse.org'

# API key of superuser account
apikey = ''

# Text or CSV file containing PIDs of datasets to be destroyed, e.g. /Users/user/Desktop/dois.txt
file = ''

destroyed_datasets = []
not_destroyed_datasets = []

print('Trying to destroy datasets...')

if '.txt' in file:
    dataset_pids = open(file)
    for dataset_pid in dataset_pids:
        dataset_pid = dataset_pid.rstrip()
        url = '%s/api/datasets/:persistentId/destroy/?persistentId=%s' % (server, dataset_pid)

        headers = {
            'X-Dataverse-key': apikey}

        req = urllib.request.Request(
            url=url,
            headers=headers,
            method='DELETE')

        try:
            response = urllib.request.urlopen(req)
            print('%s destroyed' % (dataset_pid))
            destroyed_datasets.append(dataset_pid)
        except Exception:
            print('Could not destroy %s' % (dataset_pid))
            not_destroyed_datasets.append(dataset_pid)

else:
    if '.csv' in file:
        with open(file, mode='r', encoding='utf-8') as f:
            csv_dict_reader = DictReader(f, delimiter=',')
            for row in csv_dict_reader:
                dataset_pid = row['persistent_id'].rstrip()
                url = '%s/api/datasets/:persistentId/destroy/?persistentId=%s' % (server, dataset_pid)

                headers = {
                    'X-Dataverse-key': apikey}

                req = urllib.request.Request(
                    url=url,
                    headers=headers,
                    method='DELETE')

                try:
                    response = urllib.request.urlopen(req)
                    print('%s destroyed' % (dataset_pid))
                    destroyed_datasets.append(dataset_pid)
                except Exception:
                    print('Could not destroy %s' % (dataset_pid))
                    not_destroyed_datasets.append(dataset_pid)

print('\nDatasets destroyed: %s' % (len(destroyed_datasets)))
if destroyed_datasets:
    print(destroyed_datasets)

print('\nDatasets not destroyed: %s' % (len(not_destroyed_datasets)))
if not_destroyed_datasets:
    print(not_destroyed_datasets)
