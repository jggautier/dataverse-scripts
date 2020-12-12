'''
Delete the dataverses in a given .txt file or CSV file that includes
a list or column of dataverse aliases
'''

from csv import DictReader
import urllib.request

file = ''  # Path to file with aliases of dataverses to be deleted
server = ''  # Base URL of repository hosting the dataverses to be deleted
apikey = ''  # Superuser API key

# Read lines in .txt file or column named 'dataverse_alias' in .csv file
dataverseAliases = []

if '.txt' in file:
    total = len(open(file).readlines())
    dataverseInfo = open(file)
    for dataverseAlias in dataverseInfo:
        dataverseAlias = dataverseAlias.rstrip()
        dataverseAliases.append(dataverseAlias)

if '.csv' in file:
    with open(file, mode='r', encoding='utf-8') as f:
        total = len(f.readlines()) - 1

    with open(file, mode='r', encoding='utf-8') as f:
        dataverseInfo = DictReader(f, delimiter=',')
        for dataverse in dataverseInfo:
            dataverseAlias = dataverse['dataverse_alias']
            dataverseAliases.append(dataverseAlias)

# Create variables for the script's progress
deletedDataverses = []
notDeletedDataverses = []
count = 0

# For each dataverseAlias in dataverseAliases list...
for dataverseAlias in dataverseAliases:
    count += 1

    url = '%s/api/dataverses/%s' % (server, dataverseAlias)

    headers = {'X-Dataverse-key': apikey}

    req = urllib.request.Request(
        url=url,
        headers=headers,
        method='DELETE')

    # Try to delete the dataverse
    try:
        response = urllib.request.urlopen(req)
        print('%s of %s: Deleted - %s' % (count, total, dataverseAlias))
        deletedDataverses.append(dataverseAlias)

    # Or save alias of dataverse that failes to delete
    except Exception:
        print('%s of %s: Could not be deleted - %s' % (count, total, dataverseAlias))
        notDeletedDataverses.append(dataverseAlias)

# Print results
print('Dataverses deleted: %s' % (len(deletedDataverses)))

if notDeletedDataverses:
    print('Count of dataverses not deleted: %s' % (len(notDeletedDataverses)))
    print(notDeletedDataverses)
