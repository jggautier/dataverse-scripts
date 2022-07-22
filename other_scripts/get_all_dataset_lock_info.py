import csv
from dateutil import tz
from dateutil.parser import parse
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import json
import os
import requests
import time
import sys

sys.path.append('/Users/juliangautier/dataverse-scripts/dataverse_repository_curation_assistant')

from dataverse_repository_curation_assistant_functions import *

# From user get installation URL, apiToken, directory to save CSV file
installationUrl = ''
apiKey = ''
directoryPath = ''

# To search RT system for emails that locked dataset owners have sent to Dataverse support,
# include your RT username and password
rtUserLogin = ''
rtUserPassword = ''

# List PIDs of datasets whose problematic locks have already been reported
# e.g. in the Harvard Dataverse Repository GitHub repo issue at https://github.com/IQSS/dataverse.harvard.edu/issues/150)
ignorePIDs = [
    'doi:10.7910/DVN/GLMW3X', 
    'doi:10.7910/DVN/A3NWA7',
    'doi:10.7910/DVN/VYNLON',
    'doi:10.7910/DVN/RC0WLY'
    ]

# List lock types. See https://guides.dataverse.org/en/5.10/api/native-api.html?highlight=locks#list-locks-across-all-datasets
lockTypesList = ['Ingest', 'finalizePublication']

currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

lockedDatasetPids = []
lockTypesString = list_to_string(lockTypesList)

# Get dataset PIDs of datasets that have any of the lock types in lockTypesList
print(f'Getting information about datasets with the lock types: {lockTypesString}')
for lockType in lockTypesList:

    datasetLocksApiEndpoint = f'{installationUrl}/api/datasets/locks?type={lockType}'
    response = requests.get(
        datasetLocksApiEndpoint,
        headers={'X-Dataverse-key': apiKey})
    data = response.json()

    if data['status'] == 'OK':
        for lock in data['data']:
            lockedDatasetPid = lock['dataset']
            lockedDatasetPids.append(lockedDatasetPid)

# Remove PIDs in ignorePIDs list from lockedDatasetPids list
lockedDatasetPids = [lockedDatasetPid for lockedDatasetPid in lockedDatasetPids if lockedDatasetPid not in ignorePIDs]

# Use set function to deduplicate lockedDatasetPids list and convert set to a list again
lockedDatasetPids = list(set(lockedDatasetPids))

total = len(lockedDatasetPids)

if total == 0:
    print(f'No locked datasets found (not including the {len(ignorePIDs)} datasets being ignored).')

elif total > 0:
    print(f'Locked datasets found: {total}\r\r')

    if rtUserLogin and rtUserPassword != '':
        import rt
        # Log in to RT to search for support emails from the dataset depositors
        print('Logging into RT support email system')
        tracker = rt.Rt('https://help.hmdc.harvard.edu/REST/1.0/', rtUserLogin, rtUserPassword)
        tracker.login()

    lockedDatasetCount = 0

    # Create CSV file and header row
    csvOutputFile = f'dataset_locked_status_{currentTime}.csv'
    csvOutputFilePath = os.path.join(directoryPath, csvOutputFile)

    with open(csvOutputFilePath, mode='w', newline='') as f:
        f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        f.writerow([
            'dataset_url', 'dataset_title', 'lock_reason', 'locked_date', 'user_name',
            'contact_email', 'possible_duplicate_datasets', 'rtticket_urls'])

        # For each dataset, write to the CSV file info about each lock the dataset has
        for lockedDatasetPid in lockedDatasetPids:
            lockedDatasetCount += 1

            print(f'\rGetting information about {lockedDatasetCount} of {total} datasets: {lockedDatasetPid}')

            print('\tGetting dataset title and contact information')
            datasetMetadata = get_dataset_metadata_export(
                installationUrl=installationUrl, datasetPid=lockedDatasetPid, 
                exportFormat='dataverse_json', header={}, apiKey=apiKey)

            # Get title of latest version of the dataset
            for field in datasetMetadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
                if field['typeName'] == 'title':
                    lockedDatasetTitle = field['value']

            # Get contact email addresses of the dataset
            contactEmailsList = []

            for field in datasetMetadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
                if field['typeName'] == 'datasetContact':
                    for contact in field['value']:
                        contactEmail = contact['datasetContactEmail']['value']
                        contactEmailsList.append(contactEmail)
            contactEmailsString = list_to_string(contactEmailsList)

            # If RT username and password is provided, log into RT and use the contact email addresses to
            # search for support emails from the dataset owner
            if rtUserLogin and rtUserPassword != '':
                
                print('\tSearching for related emails in the RT support email system')
                rtTicketUrlsList = []
                for contactEmail in contactEmailsList:

                    # Search RT system for emails sent from the contact email address
                    searchResults = tracker.search(
                        Queue='dataverse_support', 
                        raw_query=f'Requestor.EmailAddress="{contactEmail}"')

                    # If there are any RT tickets found, save the ticket URL
                    if len(searchResults) > 0:
                        for rtTicket in searchResults:
                            rtTicketID = rtTicket['numerical_id']
                            rtTicketUrl = f'https://help.hmdc.harvard.edu/Ticket/Display.html?id={rtTicketID}'
                            rtTicketUrlsList.append(rtTicketUrl)

                        # Use set function to deduplicate rtTicketUrlsList list and convert set to a list again
                        rtTicketUrlsList = list(set(rtTicketUrlsList))

                        # Convert list of ticket URLs to a string (to add to CSV file later)
                        rtTicketUrlsString = list_to_string(rtTicketUrlsList)
                    if len(searchResults) == 0:
                        rtTicketUrlsString = 'No RT tickets found'

            # If no RT username or password are provided...
            elif rtUserLogin or rtUserPassword == '':
                rtTicketUrlsString = 'Not logged into RT. Provide RT username and password'

            # Get all data about locks on the dataset
            url = f'{installationUrl}/api/datasets/:persistentId/locks?persistentId={lockedDatasetPid}'
            allLockData = requests.get(url).json()
            print('\tGetting information about all locks on the dataset')

            for lock in allLockData['data']:
                datasetUrl = f'{installationUrl}/dataset.xhtml?persistentId={lockedDatasetPid}&version=DRAFT'
                reason = lock['lockType']
                lockedDate = convert_to_local_tz(lock['date'], shortDate=True)
                userName = lock['user']

                # Search for and return the DOIs of the depositor's datasets with similar titles
                print('\tSearching for duplicate datasets')

                userTracesApiEndpointUrl = f'{installationUrl}/api/users/{userName}/traces'

                response = requests.get(
                    userTracesApiEndpointUrl,
                    headers={'X-Dataverse-key': apiKey})
                userTracesData = response.json()

                createdDatasetPidsList = []
                if 'datasetCreator' in userTracesData['data']['traces'] and userTracesData['data']['traces']['datasetCreator']['count'] > 1:
                    for item in userTracesData['data']['traces']['datasetCreator']['items']:
                        createdDatasetPid = item['pid']
                        if createdDatasetPid != lockedDatasetPid:
                            createdDatasetPidsList.append(createdDatasetPid)

                datasetTitles = []
                potentialDuplicateDatasetsList = []

                for createdDatasetPid in createdDatasetPidsList:
                    datasetMetadata = get_dataset_metadata_export(
                        installationUrl=installationUrl, datasetPid=createdDatasetPid, 
                        exportFormat='dataverse_json', header={}, apiKey=apiKey)

                    # Get title of latest version of the dataset
                    if 'latestVersion' in datasetMetadata['data']:
                        for field in datasetMetadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
                            if field['typeName'] == 'title':
                                datasetTitle = field['value']
                                datasetTitles.append(datasetTitle)
                                tokenSetScore = fuzz.token_set_ratio(lockedDatasetTitle, datasetTitle)
                                if tokenSetScore >= 80:
                                    potentialDuplicateDatasetsList.append(createdDatasetPid)
                if len(potentialDuplicateDatasetsList) == 0:
                    potentialDuplicateDatasetsString = 'No duplicate datasets found'
                elif len(potentialDuplicateDatasetsList) > 0:
                    potentialDuplicateDatasetsString = list_to_string(potentialDuplicateDatasetsList)

                f.writerow([
                    datasetUrl, lockedDatasetTitle, reason, lockedDate, userName,
                    contactEmailsString, potentialDuplicateDatasetsString, rtTicketUrlsString])

                print('\tInformation added to CSV file')
