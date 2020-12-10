# Delete dataverses

from csv import DictReader
import urllib.request

file = ''  # Path to file with aliases of dataverses to be deleted
server = ''  # Base URL of repository hosting the dataverses to be deleted
apikey = ''  # Superuser API key

dataverseAliases = []

if '.txt' in file:
    dataverseInfo = open(file)
    total = len(dataverseInfo)
    for dataverseAlias in dataverseInfo:
        dataverseAliases.append(dataverseAlias)

if '.csv' in file:
    with open(file, mode='r', encoding='utf-8') as f:
        total = len(f.readlines()) - 1

    with open(file, mode='r', encoding='utf-8') as f:
        dataverseInfo = DictReader(f, delimiter=',')
        for dataverse in dataverseInfo:
            dataverseAlias = dataverse['dataverse_alias']
            dataverseAliases.append(dataverseAlias)

deletedDataverses = []
notDeletedDataverses = []

count = 0

for dataverseAlias in dataverseAliases:
    count += 1

    url = '%s/api/dataverses/%s' % (server, dataverseAlias)

    headers = {'X-Dataverse-key': apikey}

    req = urllib.request.Request(
        url=url,
        headers=headers,
        method='DELETE')

    try:
        response = urllib.request.urlopen(req)
        print('%s of %s: Deleted - %s' % (count, total, dataverseAlias))
        deletedDataverses.append(dataverseAlias)
    except Exception:
        print('%s of %s: Could not be deleted - %s' % (count, total, dataverseAlias))
        notDeletedDataverses.append(dataverseAlias)

print('Dataverses deleted: %s' % (len(deletedDataverses)))

if notDeletedDataverses:
    print('Count of dataverses not deleted: %s' % (len(notDeletedDataverses)))
    print(notDeletedDataverses)
