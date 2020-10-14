'''
For a given list of datasets, changes the date used in the dataset citation from the default
(date when datasets were first published in the Dataverse repository) to the date in another date
metadata field, e.g. distributionDate
'''

from csv import DictReader
import os
import urllib.request

server = ''  # Dataverse repository URL, e.g. https://demo.dataverse.org
apikey = ''  # API key of super user account
data = b'distributionDate'  # Provide database name of date metadata field to use for citation date

file = ''  # Text file containing PIDs of datasets whose citation dates should be changed

file_name = os.path.basename(file)
citation_dates_changed = []
citation_dates_not_changed = []

print('Trying to change citation dates...')

if '.txt' in file_name:
    dataset_pids = open(file)
    count = 0
    for dataset_pid in dataset_pids:
        dataset_pid = dataset_pid.rstrip()
        url = '%s/api/datasets/:persistentId/citationdate?persistentId=%s' % (server, dataset_pid)

        headers = {
            'X-Dataverse-key': apikey}

        req = urllib.request.Request(
            url=url,
            data=data,
            headers=headers,
            method='PUT')

        try:
            response = urllib.request.urlopen(req)
            print('%s destroyed' % (dataset_pid))
            citation_dates_changed.append(dataset_pid)
        except Exception:
            print('Could not destroy %s' % (dataset_pid))
            citation_dates_not_changed.append(dataset_pid)

else:
    if '.csv' in file_name:
        with open(file, mode='r', encoding='utf-8') as f:
            csv_dict_reader = DictReader(f, delimiter=',')
            for row in csv_dict_reader:
                dataset_pid = row['persistent_id'].rstrip()
                url = '%s/api/datasets/:persistentId/citationdate?persistentId=%s' % (server, dataset_pid)

                headers = {
                    'X-Dataverse-key': apikey}

                req = urllib.request.Request(
                    url=url,
                    data=data,
                    headers=headers,
                    method='PUT')

                try:
                    response = urllib.request.urlopen(req)
                    print('%s destroyed' % (dataset_pid))
                    citation_dates_changed.append(dataset_pid)
                except Exception:
                    print('Could not destroy %s' % (dataset_pid))
                    citation_dates_not_changed.append(dataset_pid)

print('\nDatasets destroyed: %s' % (len(citation_dates_changed)))
if citation_dates_changed:
    print(citation_dates_changed)

print('Datasets not destroyed: %s' % (len(citation_dates_not_changed)))
if citation_dates_not_changed:
    print(citation_dates_not_changed)
