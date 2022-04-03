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
            status = '%s: %s' % (status, data['message'])
    except Exception:
        status = 'NA'
    return status


# Save current time for folder and file timestamps
currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

# Create the main directory that will store a directory for each installation
allInstallationsMetadataDirectory = str(Path(baseDirectory + '/' + 'all_installation_metadata_%s' % (currentTime)))
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
    installation_name = installation['name']
    hostname = installation['hostname']
    installationUrl = 'http://%s' % (hostname)
    print('\nChecking %s of %s installations: %s' % (installationProgressCount, countOfInstallations, installation_name))

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

        searchApiUrl = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=1&sort=date&order=desc' % (installationUrl)
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
        getJsonApiUrl = '%s/api/v1/datasets/:persistentId/?persistentId=%s' % (installationUrl, testDatasetPid)
        getJsonApiUrl = getJsonApiUrl.replace('//api', '/api')
        getJsonApiStatus = checkapiendpoint(getJsonApiUrl)
    else:
        getJsonApiStatus = 'NA'
    print('\t"Get dataset JSON" API status: %s' % (getJsonApiStatus))

    # If the "Get dataset JSON" endpoint works, download the installation's metadatablock JSON files, dataset PIDs, and dataset metadata

    if getJsonApiStatus == 'OK':

        # Save time and date when script started downloading from the installation to append it to the installation's directory and files
        currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

        # Create directory for the installation
        installationDirectory = allInstallationsMetadataDirectory + '/' + installation_name.replace(' ', '_') + '_%s' % (currentTime)
        os.mkdir(installationDirectory)

        # Use the "Get Version" endpoint to get installation's Dataverse version (or set version as 'NA')
        getInstallationVersionApiUrl = '%s/api/v1/info/version' % (installationUrl)
        getInstallationVersionApiUrl = getInstallationVersionApiUrl.replace('//api', '/api')
        getInstallationVersionApiStatus = checkapiendpoint(getInstallationVersionApiUrl)

        if getInstallationVersionApiStatus == 'OK':
            response = requests.get(getInstallationVersionApiUrl, headers=headers, timeout=20, verify=False)
            getInstallationVersionApiData = response.json()
            dataverseVersion = getInstallationVersionApiData['data']['version']
            dataverseVersion = str(dataverseVersion.lstrip('v'))
        else:
            dataverseVersion = 'NA'

        print('\tDataverse version: %s' % (dataverseVersion))

        # Create a directory for the installation's metadatablock files
        metadatablockFileDirectoryPath = installationDirectory + '/' + 'metadatablocks_v%s' % (dataverseVersion)
        os.mkdir(metadatablockFileDirectoryPath)

        # Download metadatablock JSON files

        # Get list of the installation's metadatablock names
        metadatablocksApi = '%s/api/v1/metadatablocks' % (installationUrl)
        metadatablocksApi = metadatablocksApi.replace('//api', '/api')

        response = requests.get(metadatablocksApi, headers=headers, timeout=20, verify=False)
        metadatablockData = response.json()

        metadatablockNames = []
        for i in metadatablockData['data']:
            metadatablockName = i['name']
            metadatablockNames.append(metadatablockName)

        print('\tDownloading metadatablock JSON file(s) into metadatablocks folder')

        for metadatablockName in metadatablockNames:
            metadatablockApiEndpointUrl = '%s/%s' % (metadatablocksApi, metadatablockName)
            response = requests.get(metadatablockApiEndpointUrl, headers=headers, timeout=20, verify=False)
            metadata = response.json()

            # If the metadatablock has fields, download the metadatablock data into a JSON file
            if len(metadata['data']['fields']) > 0:

                metadatablockFile = str(Path(metadatablockFileDirectoryPath)) + '/' '%s_v%s.json' % (metadatablockName, dataverseVersion)

                with open(metadatablockFile, mode='w') as f:
                    f.write(json.dumps(response.json(), indent=4))

        # Use the Search API to get the installation's dataset PIDs, name and alias of owning 
        # Dataverse Collection and write them to a CSV file, and use the "Get dataset JSON" 
        # endpoint to get those datasets' metadata

        # Create CSV file
        datasetPidsFile = installationDirectory + '/' + 'dataset_pids_%s_%s.csv' % (installation_name, currentTime)

        with open(datasetPidsFile, mode='w', newline='') as f1:
            f1 = csv.writer(f1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            f1.writerow(['persistent_id', 'persistentUrl', 'dataverse_name', 'dataverse_alias'])

        # Use Search API to get installation's dataset info and write it to a CSV file
        print('\tWriting %s dataset info to CSV file:' % (datasetCount))

        # Initialization for paginating through Search API results and showing progress
        start = 0
        condition = True
        dataset_pid_count = 0

        # Create variable for storing count of misindexed datasets
        misindexed_datasets_count = 0

        with open(datasetPidsFile, mode='a', encoding='utf-8', newline='') as f1:
            f1 = csv.writer(f1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            while (condition):
                try:
                    per_page = 10
                    url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=%s&start=%s&sort=date&order=desc' % (installationUrl, per_page, start)
                    response = requests.get(url, headers=headers, verify=False)
                    data = response.json()

                    # For each dataset, write the dataset info to the CSV file
                    for i in data['data']['items']:
                        persistent_id = i['global_id']
                        persistent_url = i['url']
                        dataverse_name = i.get('name_of_dataverse', 'NA')
                        dataverse_alias = i.get('identifier_of_dataverse', 'NA')

                        # Create new row with dataset and file info
                        f1.writerow([persistent_id, persistent_url, dataverse_name, dataverse_alias])

                        dataset_pid_count += 1
                        print('\t\t%s of %s' % (dataset_pid_count, datasetCount), end='\r', flush=True)

                    # Update variables to paginate through the search results
                    start = start + per_page

                # Print error message if misindexed datasets break the Search API call, and try the next page.
                # See https://github.com/IQSS/dataverse/issues/4225
                except Exception:
                    print('\t\tper_page=10 url broken. Checking per_page=1')
                    try:
                        per_page = 1
                        url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=%s&start=%s&sort=date&order=desc' % (installationUrl, per_page, start)
                        response = requests.get(url, headers=headers, timeout=20, verify=False)
                        data = response.json()

                        # For each dataset, write the dataset info to the CSV file
                        for i in data['data']['items']:
                            persistent_id = i['global_id']
                            persistent_url = i['url']
                            dataverse_name = i.get('name_of_dataverse', 'NA')
                            dataverse_alias = i.get('identifier_of_dataverse', 'NA')

                            # Create new row with dataset and file info
                            f1.writerow([persistent_id, persistent_url, dataverse_name, dataverse_alias])

                            dataset_pid_count += 1
                            print('\t\t%s of %s' % (dataset_pid_count, datasetCount), end='\r', flush=True)

                            # Update variables to paginate through the search results
                            start = start + per_page

                    except Exception:
                        misindexed_datasets_count += 1
                        start = start + per_page

                # Stop paginating when there are no more results
                condition = start < datasetCount

            print('\n\t%s dataset PIDs written to CSV file' % (datasetCount))

        if misindexed_datasets_count:
            print('\n\n\tUnretrievable dataset PIDs due to misindexing: %s\n' % (misindexed_datasets_count))

        # Create directory for dataset JSON metadata
        jsonMetadataDirectory = installationDirectory + '/' + 'JSON_metadata' + '_%s' % (currentTime)
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
                    latestVersionEndpointUrl = '%s/api/datasets/:persistentId?persistentId=%s' % (installationUrl, datasetPid)
                    response = requests.get(latestVersionEndpointUrl, headers=headers, verify=False)
                    latestVersionMetadata = response.json()
                    if latestVersionMetadata['status'] == 'OK':
                        persistentUrl = latestVersionMetadata['data']['persistentUrl']
                        publisher = latestVersionMetadata['data']['publisher']
                        publicationDate = latestVersionMetadata['data']['publicationDate']
                        metadataLanguage = improved_get(latestVersionMetadata, 'data.metadataLanguage')

                        allVersionUrl = '%s/api/datasets/:persistentId/versions?persistentId=%s' % (installationUrl, datasetPid)
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
                            version_number = majorversion + '.' + minorversion

                            metadataFile = jsonMetadataDirectory + '/' + '%s_v%s.json' % (datasetPid.replace(':', '_').replace('/', '_'), version_number)

                            # Write the JSON to the new file
                            with open(metadataFile, mode='w') as f3:
                                f3.write(json.dumps(datasetVersion, indent=4))

                    # Increase count variable to track progress
                    metadataDownloadedCount += 1

                    # Print progress
                    print('\t\tDownloaded Dataverse JSON metadata of %s of %s datasets' % (metadataDownloadedCount, datasetCount), end='\r', flush=True)

                except Exception:
                    metadataNotDownloaded.append(datasetPid)

        print('\t\tDownloaded Dataverse JSON metadata of %s of %s datasets' % (metadataDownloadedCount, datasetCount))

        if metadataNotDownloaded:
            print('The metadata of the following %s dataset(s) could not be downloaded:' % (len(metadataNotDownloaded)))
            print(metadataNotDownloaded)

    installationProgressCount += 1
