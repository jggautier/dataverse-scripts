'''
Delete the dataverses in a given .txt file or CSV file that includes
a list or column (named "id") of dataverse database IDs
'''

from csv import DictReader
import requests

server = ''  # Base URL of repository hosting the dataverses to be deleted
apikey = ''  # Superuser API key
file = ''  # Path to .txt or .csv file with database IDs of dataverses to be deleted

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

    # Try to delete the dataverse and report
    url = '%s/api/dataverses/%s' % (server, dataverseId)
    try:
        req = requests.delete(
            url,
            headers={
                'X-Dataverse-key': apikey
            })

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
