# Destroys a given list of datasets

import urllib.request

server = ''  # Dataverse repository URL, e.g. https://demo.dataverse.org
apikey = ''  # API key of super user account

file = ''  # Text file containing PIDs of datasets to be destroyed

dataset_pids = open(file)

destroyed_datasets = []
not_destroyed_datasets = []

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

print('\nDatasets destroyed: %s' % (len(destroyed_datasets)))
if destroyed_datasets:
    print(destroyed_datasets)

print('Datasets not destroyed: %s' % (len(not_destroyed_datasets)))
if not_destroyed_datasets:
    print(not_destroyed_datasets)
