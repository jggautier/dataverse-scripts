# Download dataset metadata of as many known Dataverse installations as possible

import csv
from csv import DictReader
import json
import os
from pathlib import Path
import pandas as pd
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import time
from urllib.parse import urlparse


def improved_get(_dict, path, default=None):
    for key in path.split('.'):
        try:
            _dict = _dict[key]
        except KeyError:
            return default
    return str(_dict)


# Enter directory path for installation directories and where the CSV of API keys is located
# (if on a Windows machine, use forward slashes, which will be converted to back slashes)
baseDirectory = ''  # e.g. /Users/Owner/Desktop

# Enter a user agent and your email address. Some Dataverse installations block requests from scripts.
# See https://www.whatismybrowser.com/detect/what-is-my-user-agent to get your user agent
userAgent = ''
emailAddress = ''

# Enter name of CSV file containing list of API keys for installations that require one to use certain API endpoints
apiKeysFile = ''

headers = {
    'User-Agent': userAgent,
    'From': emailAddress}


def checkapiendpoint(url):
    try:
        response = requests.get(url, headers=headers, timeout=20, verify=False)
        data = response.json()
        status = data['status']
        if status == 'ERROR':
            status = f'{status}: {data['message']}'
    except Exception:
        status = 'NA'
    return status


# Save current time for folder and file timestamps
currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

# Create the main directory that will store a directory for each installation
allInstallationsMetadataDirectory = str(Path(baseDirectory + '/' + f'all_installation_metadata_{currentTime}'))
os.mkdir(allInstallationsMetadataDirectory)

# Read CSV file containing apikeys into a dataframe and turn convert into list to compare each installation name
apiKeysFilePath = baseDirectory + '/' + apiKeysFile
apiKeysDF = pd.read_csv(apiKeysFilePath).set_index('hostname')
hostnameslist = apiKeysDF.index.tolist()

# The requests module isn't able to verify the SSL cert of some installations,
# so all requests calls in this script are set to not verify certs (verify=False)
# This suppresses the warning messages that are thrown when requests are made without verifying SSL certs
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Get JSON data that the Dataverse installations map uses
print('Getting Dataverse installation data...')
mapDataUrl = 'https://raw.githubusercontent.com/IQSS/dataverse-installations/master/data/data.json'
response = requests.get(mapDataUrl, headers=headers)
mapdata = response.json()

countOfInstallations = len(mapdata['installations'])

installationProgressCount = 1

for installation in mapdata['installations']:
    installationName = installation['name']
    hostname = installation['hostname']
    installationUrl = f'http://{hostname}'
    print(f'\nChecking {installationProgressCount} of {countOfInstallations} installations: {installationName}')

    # Get status code of installation website or report no response from website
    try:
        response = requests.get(installationUrl, headers=headers, timeout=60, verify=False)

        # Save final URL redirect to installationUrl variable
        installationUrl = response.url

        # Save only the base URL to the installationUrl variable
        o = urlparse(installationUrl)
        installationUrl = o.scheme + '://' + o.netloc

        if (response.status_code == 200 or response.status_code == 301 or response.status_code == 302):
            installationStatus = str(response.status_code)

        else:
            installationUrl = 'https://%s' % (hostname)
            try:
                response = requests.get(installationUrl, headers=headers, timeout=30, verify=False)
                if (response.status_code == 200 or response.status_code == 301 or response.status_code == 302):
                    installationStatus = str(response.status_code)
            except Exception:
                installationStatus = 'NA'

    except Exception:
        installationStatus = 'NA'
    print('\tInstallation status: ' + installationStatus)

    # If there's a good response from the installation, check if Search API works by searching for installation's non-harvested datasets
    if installationStatus != 'NA':

        # If the installation is in the dataframe of API keys, API key to header dictionary
        # to use installation's endpoints that require an API key
        if hostname in hostnameslist:
            apiKeyDF = apiKeysDF[apiKeysDF.index == hostname]
            apiKey = apiKeyDF.iloc[0]['apikey']
            headers['X-Dataverse-key'] = apiKey
        # Otherwise remove any API key from the header dictionary
        else:
            headers.pop('X-Dataverse-key', None)

        searchApiUrl = f'{installationUrl}/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=1&sort=date&order=desc'
        searchApiUrl = searchApiUrl.replace('//api', '/api')
        searchApiStatus = checkapiendpoint(searchApiUrl)
    else:
        searchApiStatus = 'NA'

    # If Search API works, from Search API query results, get count of local (non-harvested) datasets
    if searchApiStatus == 'OK':
        response = requests.get(searchApiUrl, headers=headers, timeout=20, verify=False)
        searchApiData = response.json()
        datasetCount = searchApiData['data']['total_count']
    else:
        datasetCount = 'NA'
    print('\tSearch API status: %s' % (searchApiStatus))

    # Report if the installation has no published, non-harvested datasets
    if datasetCount == 0:
        print('\nInstallation has 0 published, non-harvested datasets')

    # If there are local published datasets, get the PID of a local dataset (used to check "Get dataset JSON" endpoint)
    if datasetCount != 'NA' and datasetCount > 0:
        testDatasetPid = searchApiData['data']['items'][0]['global_id']
    else:
        testDatasetPid = 'NA'

    # If a local dataset PID can be retreived, check if "Get dataset JSON" endpoint works
    if testDatasetPid != 'NA':
        getJsonApiUrl = f'{installationUrl}/api/v1/datasets/:persistentId/?persistentId={testDatasetPid}'
        getJsonApiUrl = getJsonApiUrl.replace('//api', '/api')
        getJsonApiStatus = checkapiendpoint(getJsonApiUrl)
    else:
        getJsonApiStatus = 'NA'
    print(f'\t"Get dataset JSON" API status: {getJsonApiStatus}')

    # If the "Get dataset JSON" endpoint works, download the installation's metadatablock JSON files, dataset PIDs, and dataset metadata

    if getJsonApiStatus == 'OK':

        # Save time and date when script started downloading from the installation to append it to the installation's directory and files
        currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

        # Create directory for the installation
        installationDirectory = allInstallationsMetadataDirectory + '/' + installationName.replace(' ', '_') + f'_{currentTime}'
        os.mkdir(installationDirectory)

        # Use the "Get Version" endpoint to get installation's Dataverse version (or set version as 'NA')
        getInstallationVersionApiUrl = f'{installationUrl}/api/v1/info/version'
        getInstallationVersionApiUrl = getInstallationVersionApiUrl.replace('//api', '/api')
        getInstallationVersionApiStatus = checkapiendpoint(getInstallationVersionApiUrl)

        if getInstallationVersionApiStatus == 'OK':
            response = requests.get(getInstallationVersionApiUrl, headers=headers, timeout=20, verify=False)
            getInstallationVersionApiData = response.json()
            dataverseVersion = getInstallationVersionApiData['data']['version']
            dataverseVersion = str(dataverseVersion.lstrip('v'))
        else:
            dataverseVersion = 'NA'

        print(f'\tDataverse version: {dataverseVersion}')

        # Create a directory for the installation's metadatablock files
        metadatablockFileDirectoryPath = installationDirectory + '/' + f'metadatablocks_v{dataverseVersion}'
        os.mkdir(metadatablockFileDirectoryPath)

        # Download metadatablock JSON files

        # Get list of the installation's metadatablock names
        metadatablocksApiEndpointUrl = f'{installationUrl}/api/v1/metadatablocks'
        metadatablocksApiEndpointUrl = metadatablocksApiEndpointUrl.replace('//api', '/api')

        response = requests.get(metadatablocksApiEndpointUrl, headers=headers, timeout=20, verify=False)
        metadatablockData = response.json()

        metadatablockNames = []
        for i in metadatablockData['data']:
            metadatablockName = i['name']
            metadatablockNames.append(metadatablockName)

        print('\tDownloading metadatablock JSON file(s) into metadatablocks folder')

        for metadatablockName in metadatablockNames:
            metadatablockApiEndpointUrl = f'{metadatablocksApiEndpointUrl}/{metadatablockName}'
            response = requests.get(metadatablockApiEndpointUrl, headers=headers, timeout=20, verify=False)
            metadata = response.json()

            # If the metadatablock has fields, download the metadatablock data into a JSON file
            if len(metadata['data']['fields']) > 0:

                metadatablockFile = str(Path(metadatablockFileDirectoryPath)) + '/' f'{metadatablockName}_v{dataverseVersion}.json'

                with open(metadatablockFile, mode='w') as f:
                    f.write(json.dumps(response.json(), indent=4))

        # Use the Search API to get the installation's dataset PIDs, name and alias of owning 
        # Dataverse Collection and write them to a CSV file, and use the "Get dataset JSON" 
        # endpoint to get those datasets' metadata

        # Create CSV file
        datasetPidsFile = installationDirectory + '/' + f'dataset_pids_{installationName}_{currentTime}.csv'

        with open(datasetPidsFile, mode='w', newline='') as f1:
            f1 = csv.writer(f1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            f1.writerow(['persistent_id', 'persistentUrl', 'dataverse_name', 'dataverse_alias'])

        # Use Search API to get installation's dataset info and write it to a CSV file
        print(f'\tWriting {datasetCount} dataset info to CSV file:')

        # Initialization for paginating through Search API results and showing progress
        start = 0
        condition = True
        datasetPidCount = 0

        # Create variable for storing count of misindexed datasets
        misindexedDatasetsCount = 0

        with open(datasetPidsFile, mode='a', encoding='utf-8', newline='') as f1:
            f1 = csv.writer(f1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            while (condition):
                try:
                    perPage = 10
                    url = f'{installationUrl}/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page={perPage}&start={start}&sort=date&order=desc'
                    response = requests.get(url, headers=headers, verify=False)
                    data = response.json()

                    # For each dataset, write the dataset info to the CSV file
                    for i in data['data']['items']:
                        persistentId = i['global_id']
                        persistentUrl = i['url']
                        dataverseName = i.get('name_of_dataverse', 'NA')
                        dataverseAlias = i.get('identifier_of_dataverse', 'NA')

                        # Create new row with dataset and file info
                        f1.writerow([persistentId, persistentUrl, dataverseName, dataverseAlias])

                        datasetPidCount += 1
                        print('\t\t%s of %s' % (datasetPidCount, datasetCount), end='\r', flush=True)

                    # Update variables to paginate through the search results
                    start = start + perPage

                # Print error message if misindexed datasets break the Search API call, and try the next page.
                # See https://github.com/IQSS/dataverse/issues/4225
                except Exception:
                    print('\t\tper_page=10 url broken. Checking per_page=1')
                    try:
                        perPage = 1
                        url = f'{installationUrl}/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page={perPage}&start={start}&sort=date&order=desc'
                        response = requests.get(url, headers=headers, timeout=20, verify=False)
                        data = response.json()

                        # For each dataset, write the dataset info to the CSV file
                        for i in data['data']['items']:
                            persistentId = i['global_id']
                            persistentUrl = i['url']
                            dataverseName = i.get('name_of_dataverse', 'NA')
                            dataverseAlias = i.get('identifier_of_dataverse', 'NA')

                            # Create new row with dataset and file info
                            f1.writerow([persistentId, persistentUrl, dataverseName, dataverseAlias])

                            datasetPidCount += 1
                            print(f'\t\t{datasetPidCount} of {datasetCount}', end='\r', flush=True)

                            # Update variables to paginate through the search results
                            start = start + perPage

                    except Exception:
                        misindexedDatasetsCount += 1
                        start = start + perPage

                # Stop paginating when there are no more results
                condition = start < datasetCount

            print('\n\t%s dataset PIDs written to CSV file' % (datasetCount))

        if misindexedDatasetsCount:

            # Create txt file and list 
            print(f'\n\n\tUnretrievable dataset PIDs due to misindexing: {misindexedDatasetsCount}\n')

        # Create directory for dataset JSON metadata
        jsonMetadataDirectory = installationDirectory + '/' + 'JSON_metadata' + f'_{currentTime}' % (currentTime)
        os.mkdir(jsonMetadataDirectory)

        # For each dataset PID in CSV file, download dataset's JSON metadata
        print('\tDownloading JSON metadata to dataset_metadata folder:')

        # Initiate counts for progress indicator
        metadataDownloadedCount = 0
        metadataNotDownloaded = []

        # For each dataset persistent identifier in the CSV file, download the dataset's Dataverse JSON file into the metadata folder
        with open(datasetPidsFile, mode='r', encoding='utf-8') as f2:
            csvDictReader = DictReader(f2, delimiter=',')
            for row in csvDictReader:
                datasetPid = row['persistent_id'].rstrip()

            # Get the metadata of each version of the dataset
                try:
                    latestVersionEndpointUrl = f'{installationUrl}/api/datasets/:persistentId?persistentId={datasetPid}' % (installationUrl, datasetPid)
                    response = requests.get(latestVersionEndpointUrl, headers=headers, verify=False)
                    latestVersionMetadata = response.json()
                    if latestVersionMetadata['status'] == 'OK':
                        persistentUrl = latestVersionMetadata['data']['persistentUrl']
                        publisher = latestVersionMetadata['data']['publisher']
                        publicationDate = latestVersionMetadata['data']['publicationDate']
                        metadataLanguage = improved_get(latestVersionMetadata, 'data.metadataLanguage')

                        allVersionUrl = f'{installationUrl}/api/datasets/:persistentId/versions?persistentId={datasetPid}'
                        response = requests.get(allVersionUrl, headers=headers, verify=False)
                        allVersionsMetadata = response.json()

                        for datasetVersion in allVersionsMetadata['data']:
                            datasetVersion = {
                                'status': latestVersionMetadata['status'],
                                'data': {
                                    'persistentUrl': persistentUrl,
                                    'publisher': publisher,
                                    'publicationDate': publicationDate,
                                    'datasetVersion': datasetVersion}}

                            # If there's a metadatalanguage, add it to the datasetVersion['data'] dict
                            if metadataLanguage is not None:
                                datasetVersion['data']['metadataLanguage'] = metadataLanguage

                            majorversion = str(datasetVersion['data']['datasetVersion']['versionNumber'])
                            minorversion = str(datasetVersion['data']['datasetVersion']['versionMinorNumber'])
                            versionNumber = majorversion + '.' + minorversion

                            metadataFile = jsonMetadataDirectory + '/' + f'{datasetPid.replace(':', '_').replace('/', '_')}_v{versionNumber}.json'

                            # Write the JSON to the new file
                            with open(metadataFile, mode='w') as f3:
                                f3.write(json.dumps(datasetVersion, indent=4))

                    # Increase count variable to track progress
                    metadataDownloadedCount += 1

                    # Print progress
                    print(f'\t\tDownloaded Dataverse JSON metadata of {metadataDownloadedCount} of {datasetCount} datasets', end='\r', flush=True)

                except Exception:
                    metadataNotDownloaded.append(datasetPid)

        print(f'\t\tDownloaded Dataverse JSON metadata of {metadataDownloadedCount} of {datasetCount} datasets' % (metadataDownloadedCount, datasetCount))

        if metadataNotDownloaded:
            print(f'The metadata of the following {len(metadataNotDownloaded)} dataset(s) could not be downloaded:'
            print(metadataNotDownloaded)

    installationProgressCount += 1
