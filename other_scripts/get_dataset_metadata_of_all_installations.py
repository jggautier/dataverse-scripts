# Download dataset metadata of as many known Dataverse installations as possible

import contextlib
import csv
from csv import DictReader
import joblib
from joblib import Parallel, delayed
import json
import os
from pathlib import Path
import pandas as pd
import requests
import sys
import time
from tqdm import tqdm
from urllib.parse import urlparse
sys.path.append('/Users/juliangautier/dataverse-scripts/dataverse_repository_curation_assistant')

from dataverse_repository_curation_assistant_functions import *

from requests.packages.urllib3.exceptions import InsecureRequestWarning
# The requests module isn't able to verify the SSL cert of some installations,
# so all requests calls in this script are set to not verify certs (verify=False)
# This suppresses the warning messages that are thrown when requests are made without verifying SSL certs
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def check_api_endpoint(url, headers, verify=True, json_response=True):
    try:
        response = requests.get(url, headers=headers, timeout=60, verify=verify)
        if response.status_code == 200 and json_response is True:
            try:
                status = response.json()['status']
            except Exception as e:
                status = e
        elif response.status_code == 200 and json_response is False:
            status = 'OK'
        else:
            status = response.status_code
    except Exception as e:
        status = e

    return status


# Not using and haven't tested this function
# See if installation's API endpoint for getting metadata in given exports is working
def get_metadata_export_api_status(installationUrl, exportFormat, testDatasetPid):
    getMetadataExportApiUrl = f'{installationUrl}/api/datasets/export?exporter={exportFormat}&persistentId={testDatasetPid}'
    getMetadataExportApiUrl = getschemaorgApiUrl.replace('//api', '/api')
    getMetadataExportApiStatus = check_api_endpoint(getMetadataExportApiUrl, verify=False)
    return getMetadataExportApiStatus


def get_dataset_info_dict(start, headers):
    searchApiUrl = f'{installationUrl}/api/search'
    try:
        perPage = 10

        params = {
            'q': '*',
            'fq': ['-metadataSource:"Harvested"'],
            'type': ['dataset'],
            'per_page': perPage,
            'start': start}

        response = requests.get(
            searchApiUrl,
            params=params,
            headers=headers,
            verify=False)

        searchApiUrlData = response.json()

        # For each dataset, write the dataset info to the CSV file
        for i in searchApiUrlData['data']['items']:

            datasetPids.append(i['global_id'])

            newRow = {
                'dataset_pid': i['global_id'],
                'dataset_pid_url': i['url'],
                'dataverse_alias': i.get('identifier_of_dataverse', 'NA'),
                'dataverse_name': i.get('name_of_dataverse', 'NA')}
            datasetInfoDict.append(dict(newRow))

    # Print error message if misindexed datasets break the Search API call, and try the next page.
    # See https://github.com/IQSS/dataverse/issues/4225

    except Exception as e:
        print(f'per_page=10 url broken: {searchApiUrl}, {e}')

        # This code hasn't been tested because I haven't encountered Search API results with misindexed objects
        # since rewriting this code to use the joblib library
        for i in range(10):
            try:
                perPage = 1
                params['start'] = start + i

                response = requests.get(
                    searchApiUrl,
                    params=params,
                    headers=headers,
                    verify=False)

                response = requests.get(searchApiUrl)
                data = response.json()

                # For each dataset, write the dataset info to the CSV file
                for i in data['data']['items']:

                    datasetPids.append(i['global_id'])

                    newRow = {
                        'dataset_pid': i['global_id'],
                        'dataset_pid_url': i['url'],
                        'dataverse_alias': i.get('identifier_of_dataverse', 'NA'),
                        'dataverse_name': i.get('name_of_dataverse', 'NA')}
                    datasetInfoDict.append(dict(newRow))

            except Exception:
                print(searchApiUrl)
                misindexedDatasetsCount += 1


# Get directory that this Python script is in
currrentWorkingDirectory = os.getcwd()

# Enter a user agent and your email address. Some Dataverse installations block requests from scripts.
# See https://www.whatismybrowser.com/detect/what-is-my-user-agent to get your user agent
userAgent = ''
emailAddress = ''

headers = {
    'User-Agent': userAgent,
    'From': emailAddress}

# Enter name of CSV file containing list of API keys for installations that require one to use certain API endpoints
apiKeysFilePath = str(Path(currrentWorkingDirectory + '/' + 'dvinstallations_extra_info.csv'))


# Save current time for folder and file timestamps
currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

# Create the main directory that will store a directory for each installation
allInstallationsMetadataDirectory = str(Path(currrentWorkingDirectory + '/' + f'all_installation_metadata_{currentTime}'))
os.mkdir(allInstallationsMetadataDirectory)

# Read CSV file containing apikeys into a dataframe and convert to list to compare each installation name
apiKeysDF = pd.read_csv(apiKeysFilePath).set_index('hostname')
installationsRequiringApiKeyList = apiKeysDF.index.tolist()

# Get JSON data that the Dataverse installations map uses
print('Getting Dataverse installation data...')
mapDataUrl = 'https://raw.githubusercontent.com/IQSS/dataverse-installations/main/data/data.json'
response = requests.get(mapDataUrl, headers=headers)
mapdata = response.json()

countOfInstallations = len(mapData['installations'])

installationProgressCount = 1

for installation in mapData['installations']:
    installationName = installation['name']
    hostname = installation['hostname']
    
    print(f'\nChecking {installationProgressCount} of {countOfInstallations} installations: {installationName}')

    try:
        installationUrl = f'https://{hostname}'
        response = requests.get(installationUrl, headers=headers, timeout=60, verify=False)
        installationStatus = response.status_code

        # If installationStatus is bad and there're redirects, get the url of the final redirect
        if installationStatus != 200 and len(response.history) > 1:
            installationUrl = response.url
            response = requests.get(installationUrl, headers=headers, timeout=60, verify=False)
            installationStatus = response.status_code
    
    except Exception as e:
        installationStatus = e

    if installationStatus != 200:
        try:
            installationUrl = f'http://{hostname}'
            response = requests.get(installationUrl, headers=headers, timeout=60, verify=False)
            installationStatus = response.status_code
            # If there's one or more redirects, get the url of the final redirect
            if installationStatus != 200 and len(response.history) > 1:
                installationUrl = response.url

        except Exception as e:
            installationStatus = e

    print(f'Installation status for {installationUrl}: ' + str(installationStatus))

    # If there's a good response from the installation, check if Search API works by searching for installation's non-harvested datasets
    if installationStatus == 200:

        # If the installation is in the dataframe of API keys, add API key to header dictionary
        # to use installation's API endpoints, which require an API key
        if hostname in installationsRequiringApiKeyList:
            apiKeyDF = apiKeysDF[apiKeysDF.index == hostname]
            apiKey = apiKeyDF.iloc[0]['apikey']
            headers['X-Dataverse-key'] = apiKey

        # Otherwise remove any API key from the header dictionary
        else:
            headers.pop('X-Dataverse-key', None)

        # Use the "Get Version" endpoint to get installation's Dataverse version (or set version as 'NA')
        getInstallationVersionApiUrl = f'{installationUrl}/api/v1/info/version'
        getInstallationVersionApiUrl = getInstallationVersionApiUrl.replace('//api', '/api')
        getInstallationVersionApiStatus = check_api_endpoint(getInstallationVersionApiUrl, headers, verify=False, json_response=True)

        if getInstallationVersionApiStatus == 'OK':
            response = requests.get(getInstallationVersionApiUrl, headers=headers, timeout=20, verify=False)
            getInstallationVersionApiData = response.json()
            dataverseVersion = getInstallationVersionApiData['data']['version']
            dataverseVersion = str(dataverseVersion.lstrip('v'))
        else:
            dataverseVersion = 'NA'

        print(f'Dataverse version: {dataverseVersion}')

        # Check if Search API works for the installation
        searchApiCheckUrl = f'{installationUrl}/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=1&sort=date&order=desc'
        searchApiCheckUrl = searchApiCheckUrl.replace('//api', '/api')
        searchApiStatus = check_api_endpoint(searchApiCheckUrl, headers, verify=False, json_response=True)

        # If Search API works, from Search API query results, get count of local (non-harvested) datasets
        if searchApiStatus == 'OK':
            response = requests.get(searchApiCheckUrl, headers=headers, timeout=20, verify=False)
            searchApiData = response.json()
            datasetCount = searchApiData['data']['total_count']
        else:
            datasetCount = 'NA'
        print(f'\nSearch API status: {searchApiStatus}')

        # Report if the installation has no published, non-harvested datasets
        if datasetCount == 0:
            print('\nInstallation has 0 published, non-harvested datasets')

        # If there are local published datasets, get the PID of a local dataset (used later to check endpoints for getting dataset metadata)
        if datasetCount != 'NA' and datasetCount > 0:
            testDatasetPid = searchApiData['data']['items'][0]['global_id']
        else:
            testDatasetPid = 'NA'

        # If a local dataset PID can be retreived, check if "Get dataset JSON" metadata export endpoints works
        if testDatasetPid != 'NA':
            getJsonApiUrl = f'{installationUrl}/api/v1/datasets/:persistentId/?persistentId={testDatasetPid}'
            getJsonApiUrl = getJsonApiUrl.replace('//api', '/api')
            getDataverseJsonApiStatus = check_api_endpoint(getJsonApiUrl, headers, verify=False, json_response=True)

        else:
            getDataverseJsonApiStatus = 'NA'
        print(f'"Get dataset JSON" API status: {getDataverseJsonApiStatus}')

        # If the "Get dataset JSON" endpoint works, download the installation's metadatablock JSON files, dataset PIDs, and dataset metadata

        if getDataverseJsonApiStatus == 'OK':

            # Save time and date when script started downloading from the installation to append it to the installation's directory and files
            currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

            # Create directory for the installation
            installationNameTemp = installationName.replace(' ', '_')
            installationDirectory = f'{allInstallationsMetadataDirectory}/{installationNameTemp}_{currentTime}'
            os.mkdir(installationDirectory)

            # Check if endpoint for getting installation's metadatablock files works and if so save metadatablock files
            # in a directory

            # Check API endpoint for getting metadatablock data
            metadatablocksApiEndpointUrl = f'{installationUrl}/api/v1/metadatablocks'
            metadatablocksApiEndpointUrl = metadatablocksApiEndpointUrl.replace('//api', '/api')
            getMetadatablocksApiStatus = check_api_endpoint(metadatablocksApiEndpointUrl, headers, verify=False, json_response=True)

            # If API endpoint for getting metadatablock files works...
            if getMetadatablocksApiStatus == 'OK':        

                # Create a directory for the installation's metadatablock files
                metadatablockFileDirectoryPath = f'{installationDirectory}/metadatablocks_v{dataverseVersion}'
                os.mkdir(metadatablockFileDirectoryPath)

                # Download metadatablock JSON files
                response = requests.get(metadatablocksApiEndpointUrl, headers=headers, timeout=20, verify=False)
                metadatablockData = response.json()

                # Get list of the installation's metadatablock names
                metadatablockNames = []
                for i in metadatablockData['data']:
                    metadatablockName = i['name']
                    metadatablockNames.append(metadatablockName)

                print('\nDownloading metadatablock JSON files into metadatablocks folder')

                for metadatablockName in metadatablockNames:
                    metadatablockApiEndpointUrl = f'{metadatablocksApiEndpointUrl}/{metadatablockName}'
                    response = requests.get(metadatablockApiEndpointUrl, headers=headers, timeout=20, verify=False)
                    metadata = response.json()

                    # If the metadatablock has fields, download the metadatablock data into a JSON file
                    if len(metadata['data']['fields']) > 0:

                        metadatablockFile = f'{str(Path(metadatablockFileDirectoryPath))}/{metadatablockName}_v{dataverseVersion}.json'

                        with open(metadatablockFile, mode='w') as f:
                            f.write(json.dumps(response.json(), indent=4))

            # Use the Search API to get the installation's dataset PIDs, name and alias of owning 
            # Dataverse Collection and write them to a CSV file, and use the "Get dataset JSON" 
            # endpoint to get those datasets' metadata

            # Create start variables to paginate through SearchAPI results
            start = 0
            apiCallsCount = round(datasetCount/10)
            startsList = [0]
            for apiCall in range(apiCallsCount):
                start = start + 10
                startsList.append(start)
            startsListCount = len(startsList)

            print(f'\nSearching through {startsListCount} Search API page(s) to save info of {datasetCount} dataset(s) to CSV file:')

            misindexedDatasetsCount = 0
            datasetInfoDict = []
            datasetPids = []

            with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=startsListCount)) as progress_bar:
                Parallel(n_jobs=4, backend='threading')(delayed(get_dataset_info_dict)(start, headers=headers) for start in startsList)
    
            # If there's a difference, print unique count and explain how this might've happened
            datasetPids = list(set(datasetPids))
            if len(datasetPids) != datasetCount:
                print(f'Unique dataset PIDs found: {len(datasetPids)}. The Search API lists one or more datasets more than once')

            # Create dataframe from datasetInfoDict, which lists dataset basic info from Search API.
            # And remove duplicate rows from the dataframe. At least one repository has two published versions of the same dataset indexed. 
            # See https://dataverse.rhi.hi.is/dataverse/root/?q=1.00002
            datasetPidsFileDF = pd.DataFrame(datasetInfoDict).set_index('dataset_pid').drop_duplicates()

            # Export datasetPidsFileDF as a CSV file...
            datasetPidsFile = f'{installationDirectory}/dataset_pids_{installationNameTemp}_{currentTime}.csv'
            datasetPidsFileDF.to_csv(datasetPidsFile, index=True)

            # Get new dataset count based on number of PIDs saved from Search API
            datasetCount = len(datasetPids)

            if misindexedDatasetsCount > 0:

                # Create txt file and list
                print(f'\n\nUnretrievable dataset PIDs due to misindexing: {misindexedDatasetsCount}\n')

            # Create directory for dataset JSON metadata
            dataverseJsonMetadataDirectory = f'{installationDirectory}/Dataverse_JSON_metadata_{currentTime}'
            os.mkdir(dataverseJsonMetadataDirectory)

            # For each dataset PID in CSV file, download dataset's Dataverse JSON metadata
            print('\nDownloading Dataverse JSON metadata to Dataverse_JSON_metadata folder:')

            # Initiate counts for progress indicator
            dataverseJsonMetadataNotDownloaded = []

            # Create CSV file for recording if dataset metadata was downloaded
            downloadStatusFilePath = f'{installationDirectory}/download_status_{installationName}_{currentTime}.csv'

            # Create CSV file and add headerrow
            headerRow = ['dataset_pid', 'dataverse_json_export_saved']
            with open(downloadStatusFilePath, mode='w', newline='') as downloadStatusFile:
                writer = csv.writer(downloadStatusFile)
                writer.writerow(headerRow)

            save_dataset_exports(
                directoryPath=dataverseJsonMetadataDirectory,
                downloadStatusFilePath=downloadStatusFilePath,
                installationUrl=installationUrl, 
                datasetPidList=datasetPids, 
                exportFormat='dataverse_json', 
                verify=False, 
                allVersions=True, 
                header=headers, 
                apiKey='')

            # If any dataset metadata was not downloaded...
            if len(dataverseJsonMetadataNotDownloaded) > 0:
                # ... get and print a count of those dataset's
                dataverseJsonMetadataNotDownloadedCount = len(dataverseJsonMetadataNotDownloaded)
                print(f'Some metadata could not be downloaded: {dataverseJsonMetadataNotDownloadedCount}')

            # Create dataframe from downloadStatusFilePath
            downloadProgressDF = pd.read_csv(downloadStatusFilePath, sep=',', na_filter = False)

            # Merge datasetPidsFileDF and downloadProgressDF
            merged = pd.merge(datasetPidsFileDF, downloadProgressDF, how='left', on='dataset_pid')

            # Export merged dataframe (overwriting old datasetPidsFile)
            merged.to_csv(datasetPidsFile, index=False)

            # Delete downloadProgress CSV file since its been merged with datasetPidsFile
            os.remove(downloadStatusFilePath)

    installationProgressCount += 1
    print('\n----------------------')
