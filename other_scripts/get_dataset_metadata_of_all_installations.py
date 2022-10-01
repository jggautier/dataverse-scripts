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
import time
from tqdm import tqdm
from urllib.parse import urlparse

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

# Not using and haven't tested this function to gets different types of metadata exports 
def get_dataset_metadata_export(installationUrl, datasetPid, exportFormat, header={}):
    if apiKey:
        header['X-Dataverse-key'] = apiKey

    if exportFormat == 'dataverse_json':
        getJsonRepresentationOfADatasetEndpoint = '%s/api/datasets/:persistentId/?persistentId=%s' % (installationUrl, datasetPid)
        getJsonRepresentationOfADatasetEndpoint = getJsonRepresentationOfADatasetEndpoint.replace('//api', '/api')
        response = requests.get(
            getJsonRepresentationOfADatasetEndpoint,
            headers=header,
            verify=False)
        if response.status_code in (200, 401): # 401 is the unauthorized code. Valid API key is needed
            data = response.json()
        else:
            data = 'ERROR'

        return data

    # For getting metadata from other exports, which are available only for each dataset's latest published
    #  versions (whereas Dataverse JSON export is available for unpublished versions)
    if exportFormat != 'dataverse_json':
        datasetMetadataExportEndpoint = '%s/api/datasets/export?exporter=%s&persistentId=%s' % (installationUrl, exportFormat, datasetPid)
        datasetMetadataExportEndpoint = datasetMetadataExportEndpoint.replace('//api', '/api')
       
        response = requests.get(
            datasetMetadataExportEndpoint,
            headers=header,
            verify=False)

        if response.status_code == 200:
            
            if exportFormat in ('schema.org' , 'OAI_ORE'):
                data = response.json()

            if exportFormat in ('ddi' , 'oai_ddi', 'dcterms', 'oai_dc', 'Datacite', 'oai_datacite'):
                string = response.text
                data = BeautifulSoup(string, 'xml').prettify()
        else:
            data = 'ERROR'

        return data


def improved_get(_dict, path, default=None):
    for key in path.split('.'):
        try:
            _dict = _dict[key]
        except KeyError:
            return default
    return str(_dict)


def list_to_string(lst): 
    string = ', '.join(lst)
    return string


# Context manager to patch joblib to report into tqdm progress bar given as argument
@contextlib.contextmanager
def tqdm_joblib(tqdm_object):
    class TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
        def __call__(self, *args, **kwargs):
            tqdm_object.update(n=self.batch_size)
            return super().__call__(*args, **kwargs)

    old_batch_callback = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
    try:
        yield tqdm_object
    finally:
        joblib.parallel.BatchCompletionCallBack = old_batch_callback
        tqdm_object.close()


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
                'persistent_id': i['global_id'],
                'persistent_url': i['url'],
                'dataverse_alias': i.get('identifier_of_dataverse', 'NA'),
                'dataverse_name': i.get('name_of_dataverse', 'NA'),
                'dataverse_json_export_saved': True}
            datasetInfoDict.append(dict(newRow))

    # Print error message if misindexed datasets break the Search API call, and try the next page.
    # See https://github.com/IQSS/dataverse/issues/4225
    except Exception as e:
        print(f'per_page=10 url broken: {searchApiUrl}, {e}')

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
                        'persistent_id': i['global_id'],
                        'persistent_url': i['url'],
                        'dataverse_alias': i.get('identifier_of_dataverse', 'NA'),
                        'dataverse_name': i.get('name_of_dataverse', 'NA'),
                        'dataverse_json_export_saved': True}
                    datasetInfoDict.append(dict(newRow))

            except Exception:
                print(searchApiUrl)
                misindexedDatasetsCount += 1
                pass


def download_dataset_metadata_export(datasetPid, allVersions=True):
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Get the Dataverse JSON metadata of each version of the dataset
    try:
        latestVersionEndpointUrl = f'{installationUrl}/api/datasets/:persistentId?persistentId={datasetPid}'
        response = requests.get(latestVersionEndpointUrl, headers=headers, verify=False)
        latestVersionMetadata = response.json()
        if latestVersionMetadata['status'] == 'OK':
            persistentUrl = latestVersionMetadata['data']['persistentUrl']
            publisher = latestVersionMetadata['data']['publisher']
            publicationDate = latestVersionMetadata['data']['publicationDate']
            metadataLanguage = improved_get(latestVersionMetadata, 'data.metadataLanguage')

            if allVersions == False:
                datasetPidForFile = datasetPid.replace(':', '_').replace('/', '_')
                metadataFile = f'{dataverseJsonMetadataDirectory}/{datasetPidForFile}.json'

                # Write the JSON to the new file
                with open(metadataFile, mode='w') as f:
                    f.write(json.dumps(latestVersionMetadata, indent=4))

            elif allVersions == True:
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
                    versionNumber = f'{majorversion}.{minorversion}'

                    datasetPidForFile = datasetPid.replace(':', '_').replace('/', '_')
                    metadataFile = f'{dataverseJsonMetadataDirectory}/{datasetPidForFile}_v{versionNumber}.json'

                    # Write the JSON to the new file
                    with open(metadataFile, mode='w') as f:
                        f.write(json.dumps(datasetVersion, indent=4))

        elif latestVersionMetadata['status'] == 'ERROR':
            dataverseJsonMetadataNotDownloaded.append(datasetPid)

    except Exception:
        print(f'Metadata could not be downloaded for {datasetPid}')
        dataverseJsonMetadataNotDownloaded.append(datasetPid)


# Get directory that this Python script is in
currrentWorkingDirectory = os.getcwd()

# Enter a user agent and your email address. Some Dataverse installations block requests from scripts.
# See https://www.whatismybrowser.com/detect/what-is-my-user-agent to get your user agent
userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
emailAddress = 'juliangautier@g.harvard.edu'

# Enter name of CSV file containing list of API keys for installations that require one to use certain API endpoints
apiKeysFilePath = str(Path(currrentWorkingDirectory + '/' + 'dvinstallations_extra_info.csv'))

headers = {
    'User-Agent': userAgent,
    'From': emailAddress}

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
mapDataUrl = 'https://raw.githubusercontent.com/IQSS/dataverse-installations/master/data/data.json'
response = requests.get(mapDataUrl, headers=headers)
mapdata = response.json()

countOfInstallations = len(mapdata['installations'])

installationProgressCount = 1

for installation in mapdata['installations']:
    installationName = installation['name']
    hostname = installation['hostname']
    
    print(f'\nChecking {installationProgressCount} of {countOfInstallations} installations: {installationName}')

    try:
        installationUrl = f'https://{hostname}'
        response = requests.get(installationUrl, headers=headers, timeout=60, verify=False)
        installationStatus = response.status_code
        # If there's one or more redirects, get the url of the final redirect
        if response.history:
            installationUrl = response.url
    
    except Exception as e:
        installationStatus = e

    if installationStatus != 200:

        try:
            installationUrl = f'http://{hostname}'
            response = requests.get(installationUrl, headers=headers, timeout=60, verify=False)
            installationStatus = response.status_code
            # If there's one or more redirects, get the url of the final redirect
            if response.history:
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
            # installationDirectory = allInstallationsMetadataDirectory + '/' + installationName.replace(' ', '_') + f'_{currentTime}'
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

            # Use Search API to get installation's dataset info and write it to a CSV file
            print(f'\nSaving info of {datasetCount} dataset(s) to CSV file:')

            # Initialization for paginating through Search API results and showing progress
            start = 0

            # Create start variables to paginate through SearchAPI results
            apiCallsCount = round(datasetCount/10)
            startsList = [0]
            for apiCall in range(apiCallsCount):
                start = start + 10
                startsList.append(start)
            startsListCount = len(startsList)

            misindexedDatasetsCount = 0
            datasetInfoDict = []
            datasetPids = []

            with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=startsListCount)) as progress_bar:
                Parallel(n_jobs=4, backend='threading')(delayed(get_dataset_info_dict)(start, headers=headers) for start in startsList)

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

            with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=datasetCount)) as progress_bar:
                Parallel(n_jobs=4, backend='threading')(delayed(download_dataset_metadata_export)(datasetPid, allVersions=True) for datasetPid in datasetPids)

            # If any dataset's metadata was not downloaded... 
            if len(dataverseJsonMetadataNotDownloaded) > 0:
                # Print count of those dataset's
                dataverseJsonMetadataNotDownloadedCount = len(dataverseJsonMetadataNotDownloaded)
                print(f'Some metadata could not be downloaded: {dataverseJsonMetadataNotDownloadedCount}')

                # For each dataset whose metadata could not be downloaded,
                # in datasetPidsFileDF, change its dataverse_json_export_saved value to False
                for dataset in datasetInfoDict:
                    if dataset['persistent_id'] in dataverseJsonMetadataNotDownloaded:
                        dataset['dataverse_json_export_saved'] = False

            # Convert datasetInfoDict to datasetPidsFileDF...
            datasetPidsFileDF = pd.DataFrame(datasetInfoDict).set_index('persistent_id')

            # Export datasetPidsFileDF as a CSV file...
            datasetPidsFile = f'{installationDirectory}/dataset_pids_{installationName}_{currentTime}.csv'
            datasetPidsFileDF.to_csv(datasetPidsFile, index=True)

    installationProgressCount += 1
    print('\n----------------------')
