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
# and save aliases to dataverseAliases list
dataverseAliases = []

if '.txt' in file:
    dataverseInfo = open(file)
    for dataverseAlias in dataverseInfo:

        # Strip new line character so it doesn't mess with report printed in terminal
        dataverseAlias = dataverseAlias.rstrip()

        # Save alias to dataverseAlias list
        dataverseAliases.append(dataverseAlias)

if '.csv' in file:
    with open(file, mode='r', encoding='utf-8') as f:
        dataverseInfo = DictReader(f, delimiter=',')
        for dataverse in dataverseInfo:

            # Get dataverse alias from dataverse_alias column
            dataverseAlias = dataverse['dataverse_alias']

            # Save alias to dataverseAlias list
            dataverseAliases.append(dataverseAlias)

# Create variables for reporting script's progress
total = len(dataverseAliases)
deletedDataverses = []
notDeletedDataverses = []
count = 0

# For each dataverseAlias in dataverseAliases list...
for dataverseAlias in dataverseAliases:
    count += 1

    # Create URL for using delete dataverse endpoint
    url = '%s/api/dataverses/%s' % (server, dataverseAlias)

    headers = {'X-Dataverse-key': apikey}

    req = urllib.request.Request(
        url=url,
        headers=headers,
        method='DELETE')

    # Try to delete the dataverse and report
    try:
        response = urllib.request.urlopen(req)
        print('%s of %s: Deleted - %s' % (count, total, dataverseAlias))
        deletedDataverses.append(dataverseAlias)

    # If that fails, save dataverse alias to notDeletedDataverses list and report
    except Exception:
        print('%s of %s: Could not be deleted - %s' % (count, total, dataverseAlias))
        notDeletedDataverses.append(dataverseAlias)

# Print results
print('Dataverses deleted: %s' % (len(deletedDataverses)))

if notDeletedDataverses:
    print('Count of dataverses not deleted: %s' % (len(notDeletedDataverses)))
    print(notDeletedDataverses)
