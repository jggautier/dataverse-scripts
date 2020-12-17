'''
Delete the dataverses in a given .txt file or CSV file that includes
a list or column (named "id") of dataverse database IDs
'''

from csv import DictReader
import urllib.request

file = ''  # Path to .txt or .csv file with database IDs of dataverses to be deleted
server = ''  # Base URL of repository hosting the dataverses to be deleted
apikey = ''  # Superuser API key

# Read lines in .txt file or column named 'id' in .csv file
# and save IDs to dataverseIds list
dataverseIds = []

if '.txt' in file:
    dataverseInfo = open(file)
    for dataverseId in dataverseInfo:

        # Strip new line character so it doesn't mess with report printed in terminal
        dataverseId = dataverseId.rstrip()

        # Save ID to dataverseId list
        dataverseIds.append(dataverseId)

if '.csv' in file:
    with open(file, mode='r', encoding='utf-8') as f:
        dataverseInfo = DictReader(f, delimiter=',')
        for dataverse in dataverseInfo:

            # Get dataverse ID from id column
            dataverseId = dataverse['id']

            # Save ID to dataverseId list
            dataverseIds.append(dataverseId)

# Deduplicate list of dataverseIds
dataverseIds = set(dataverseIds)

# Create variables for reporting script's progress
total = len(dataverseIds)
deletedDataverses = []
notDeletedDataverses = []
count = 0

# For each dataverseId in dataverseIds list...
for dataverseId in dataverseIds:
    count += 1

    # Create URL for using delete dataverse endpoint
    url = '%s/api/dataverses/%s' % (server, dataverseId)

    headers = {'X-Dataverse-key': apikey}

    req = urllib.request.Request(
        url=url,
        headers=headers,
        method='DELETE')

    # Try to delete the dataverse and report
    try:
        response = urllib.request.urlopen(req)
        print('%s of %s: Deleted - %s' % (count, total, dataverseId))
        deletedDataverses.append(dataverseId)

    # If that fails, save ID to notDeletedDataverses list and report
    except Exception:
        print('%s of %s: Could not be deleted - %s' % (count, total, dataverseId))
        notDeletedDataverses.append(dataverseId)

# Print results
print('Dataverses deleted: %s' % (len(deletedDataverses)))

if notDeletedDataverses:
    print('Count of dataverses not deleted: %s' % (len(notDeletedDataverses)))
    print(notDeletedDataverses)
