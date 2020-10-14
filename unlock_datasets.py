# Unlocks a given list of datasets
# For more info, see http://guides.dataverse.org/en/5.0/admin/troubleshooting.html?highlight=dataset%20locks#id3

from csv import DictReader
import os
import urllib.request

# Dataverse repository URL, e.g. https://demo.dataverse.org
server = ''

# API key of user account
apikey = ''

# Text or CSV file containing PIDs of datasets to be unlocked, e.g. /Users/user/Desktop/dois.txt
file = ''

file_name = os.path.basename(file)

print('Trying to unlock datasets...')

count = 0
if '.txt' in file_name:
    dataset_pids = open(file)
    for dataset_pid in dataset_pids:
        dataset_pid = dataset_pid.rstrip()
        url = '%s/api/datasets/:persistentId/locks?persistentId=%s' % (server, dataset_pid)

        headers = {
            'X-Dataverse-key': apikey}

        req = urllib.request.Request(
            url=url,
            headers=headers,
            method='DELETE')
        try:
            response = urllib.request.urlopen(req)
            count += 1
            print('%s unlocked' % (dataset_pid))
        except Exception:
            print('Could not unlock %s' % (dataset_pid))

else:
    if '.csv' in file_name:
        with open(file, mode='r', encoding='utf-8') as f:
            csv_dict_reader = DictReader(f, delimiter=',')
            for row in csv_dict_reader:
                dataset_pid = row['persistent_id'].rstrip()
                url = '%s/api/datasets/:persistentId/locks?persistentId=%s' % (server, dataset_pid)

                headers = {
                    'X-Dataverse-key': apikey}

                req = urllib.request.Request(
                    url=url,
                    headers=headers,
                    method='DELETE')
                try:
                    response = urllib.request.urlopen(req)
                    count += 1
                    print('%s unlocked' % (dataset_pid))
                except Exception:
                    print('Could not unlock %s' % (dataset_pid))
