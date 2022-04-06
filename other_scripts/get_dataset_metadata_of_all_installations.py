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


def checkapiendpoint(url, headers, verify=True):
    response = requests.get(url, headers=headers, timeout=60, verify=verify)
    if response.status_code == 200:
        status = 'OK'
    else:
        status = 'NA'
    return status


# Not using and haven't tested this function
# See if installation's API endpoint for getting metadata in given exports is working
def get_metadata_export_api_status(installationUrl, exportFormat, testDatasetPid):
    getMetadataExportApiUrl = f'{installationUrl}/api/datasets/export?exporter={exportFormat}&persistentId={testDatasetPid}'
    getMetadataExportApiUrl = getschemaorgApiUrl.replace('//api', '/api')
    getMetadataExportApiStatus = checkapiendpoint(getMetadataExportApiUrl, verify=False)
    return getMetadataExportApiStatus

# Not using and haven't tested this function
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


# Enter directory path for installation directories and where the CSV of API keys is located
# (if on a Windows machine, use forward slashes, which will be converted to back slashes)
baseDirectory = ''  # e.g. /Users/Owner/Desktop

# Enter a user agent and your email address. Some Dataverse installations block requests from scripts.
# See https://www.whatismybrowser.com/detect/what-is-my-user-agent to get your user agent
userAgent = ''
emailAddress = ''

# Enter name of CSV file containing list of API keys for installations that require one to use certain API endpoints
apiKeysFilePath = ''

headers = {
    'User-Agent': userAgent,
    'From': emailAddress}

# Save current time for folder and file timestamps
currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

# Create the main directory that will store a directory for each installation
allInstallationsMetadataDirectory = str(Path(baseDirectory + '/' + f'all_installation_metadata_{currentTime}'))
os.mkdir(allInstallationsMetadataDirectory)

# Read CSV file containing apikeys into a dataframe and convert to list to compare each installation name
apiKeysDF = pd.read_csv(apiKeysFilePath).set_index('hostname')
hostnameslist = apiKeysDF.index.tolist()

# The requests module isn't able to verify the SSL cert of some installations,
# so all requests calls in this script are set to not verify certs (verify=False)
# This suppresses the warning messages that are thrown when requests are made without verifying SSL certs
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Get JSON data that the Dataverse installations map uses
print('Getting Dataverse installation data...')
# mapDataUrl = 'https://raw.githubusercontent.com/IQSS/dataverse-installations/master/data/data.json'
# response = requests.get(mapDataUrl, headers=headers)
# mapdata = response.json()

with open('/Users/juliangautier/Desktop/mapdata.json', 'r') as f1:  # Open each file in read mode
    mapdata = f1.read()  # Copy content to mapdata variable
    mapdata = json.loads(mapdata)  # Load content in variable as a json object

countOfInstallations = len(mapdata['installations'])

installationProgressCount = 1

for installation in mapdata['installations']:
    installationName = installation['name']
    hostname = installation['hostname']
    
    print(f'\nChecking {installationProgressCount} of {countOfInstallations} installations: {installationName}')

    try:
        installationUrl = f'http://{hostname}'
        response = requests.get(installationUrl, headers=headers, timeout=60, verify=False)
        installationStatus = response.status_code
    
    except Exception as e:
        installationStatus = e

    if installationStatus not in [200, 301, 302]:

        try:
            installationUrl = f'https://{hostname}'
            response = requests.get(installationUrl, headers=headers, timeout=60, verify=False)
            installationStatus = response.status_code

        except Exception as e:
            installationStatus = e

    print('\tInstallation status: ' + str(installationStatus))

    # If there's a good response from the installation, check if Search API works by searching for installation's non-harvested datasets
    if installationStatus in [200, 301, 302]:

        # If the installation is in the dataframe of API keys, add API key to header dictionary
        # to use installation's endpoints that require an API key
        if hostname in hostnameslist:
            apiKeyDF = apiKeysDF[apiKeysDF.index == hostname]
            apiKey = apiKeyDF.iloc[0]['apikey']
            headers['X-Dataverse-key'] = apiKey

        # Otherwise remove any API key from the header dictionary
        else:
            headers.pop('X-Dataverse-key', None)

        # Use the "Get Version" endpoint to get installation's Dataverse version (or set version as 'NA')
        getInstallationVersionApiUrl = f'{installationUrl}/api/v1/info/version'
        getInstallationVersionApiUrl = getInstallationVersionApiUrl.replace('//api', '/api')
        getInstallationVersionApiStatus = checkapiendpoint(getInstallationVersionApiUrl, headers, verify=False)

        if getInstallationVersionApiStatus == 'OK':
            response = requests.get(getInstallationVersionApiUrl, headers=headers, timeout=20, verify=False)
            getInstallationVersionApiData = response.json()
            dataverseVersion = getInstallationVersionApiData['data']['version']
            dataverseVersion = str(dataverseVersion.lstrip('v'))
        else:
            dataverseVersion = 'NA'

        print(f'\tDataverse version: {dataverseVersion}')

        # Check if Search API works for the installation
        searchApiUrl = f'{installationUrl}/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=1&sort=date&order=desc'
        searchApiUrl = searchApiUrl.replace('//api', '/api')
        searchApiStatus = checkapiendpoint(searchApiUrl, headers, verify=False)

    # If Search API works, from Search API query results, get count of local (non-harvested) datasets
    if searchApiStatus == 'OK':
        response = requests.get(searchApiUrl, headers=headers, timeout=20, verify=False)
        searchApiData = response.json()
        datasetCount = searchApiData['data']['total_count']
    else:
        datasetCount = 'NA'
    print(f'\n\tSearch API status: {searchApiStatus}')

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
        getDataverseJsonApiStatus = checkapiendpoint(getJsonApiUrl, headers, verify=False)

    else:
        getDataverseJsonApiStatus = 'NA'
    print(f'\t"Get dataset JSON" API status: {getDataverseJsonApiStatus}')

    # If the "Get dataset JSON" endpoint works, download the installation's metadatablock JSON files, dataset PIDs, and dataset metadata

    if getDataverseJsonApiStatus == 'OK':

        # Save time and date when script started downloading from the installation to append it to the installation's directory and files
        currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

        # Create directory for the installation
        installationDirectory = allInstallationsMetadataDirectory + '/' + installationName.replace(' ', '_') + f'_{currentTime}'
        os.mkdir(installationDirectory)

        # Check if endpoint for getting installation's metadatablock files works and if so save metadatablock files
        # in a directory

        # Check API endpoint for getting metadatablock data
        metadatablocksApiEndpointUrl = f'{installationUrl}/api/v1/metadatablocks'
        metadatablocksApiEndpointUrl = metadatablocksApiEndpointUrl.replace('//api', '/api')
        getMetadatablocksApiStatus = checkapiendpoint(metadatablocksApiEndpointUrl, headers, verify=False)

        # If API endpoing for getting metadatablock files works...
        if getMetadatablocksApiStatus == 'OK':        

            # Create a directory for the installation's metadatablock files
            metadatablockFileDirectoryPath = installationDirectory + '/' + f'metadatablocks_v{dataverseVersion}'
            os.mkdir(metadatablockFileDirectoryPath)

            # Download metadatablock JSON files
            response = requests.get(metadatablocksApiEndpointUrl, headers=headers, timeout=20, verify=False)
            metadatablockData = response.json()

            # Get list of the installation's metadatablock names
            metadatablockNames = []
            for i in metadatablockData['data']:
                metadatablockName = i['name']
                metadatablockNames.append(metadatablockName)

            print('\n\tDownloading metadatablock JSON files into metadatablocks folder')

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
            f1.writerow(['persistent_id', 'persistent_url', 'dataverse_name', 'dataverse_alias'])

        # Create dataframe to record if Dataverse JSON metadata for each dataset was retrieved or not
        columnNames = ['persistent_id', 'dataverse_json_export_saved']
        dataverseJsonExportSavedDF = pd.DataFrame(columns=columnNames)

        # Use Search API to get installation's dataset info and write it to a CSV file
        print(f'\n\tSaving info of {datasetCount} dataset(s) to CSV file:')

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
                        print(f'\t\t{datasetPidCount} of {datasetCount}', end='\r', flush=True)

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

            print(f'\n\tInfo of {datasetCount} dataset(s) written to CSV file')

        if misindexedDatasetsCount:

            # Create txt file and list 
            print(f'\n\n\tUnretrievable dataset PIDs due to misindexing: {misindexedDatasetsCount}\n')

        # Create directory for dataset JSON metadata
        dataverseJsonMetadataDirectory = installationDirectory + '/' + 'Dataverse_JSON_metadata' + f'_{currentTime}'
        os.mkdir(dataverseJsonMetadataDirectory)

        # For each dataset PID in CSV file, download dataset's Dataverse JSON metadata
        print('\n\tDownloading Dataverse JSON metadata to dataset_metadata folder:')

        # Initiate counts for progress indicator
        dataverseJsonmMetadataDownloadedCount = 0
        dataverseJsonMetadataNotDownloaded = []

        # For each dataset persistent identifier in the CSV file, download the dataset's Dataverse JSON file into the metadata folder
        with open(datasetPidsFile, mode='r', encoding='utf-8') as f2:
            csvDictReader = DictReader(f2, delimiter=',')
            for row in csvDictReader:
                datasetPid = row['persistent_id'].rstrip()

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

                            datasetPidForFile = datasetPid.replace(':', '_').replace('/', '_')
                            metadataFile = dataverseJsonMetadataDirectory + '/' + f'{datasetPidForFile}_v{versionNumber}.json'

                            # Write the JSON to the new file
                            with open(metadataFile, mode='w') as f3:
                                f3.write(json.dumps(datasetVersion, indent=4))

                        # Increase count variable to track progress
                        dataverseJsonmMetadataDownloadedCount += 1
                        dataverseJsonExportSaved = True

                        # Write to datasetPidsFile, in the column for this export, that the metadata dataset was retrieved

                    # Print progress
                    print(f'\t\tDownloaded Dataverse JSON metadata of {dataverseJsonmMetadataDownloadedCount} of {datasetCount} datasets', end='\r', flush=True)

                except Exception:
                    dataverseJsonMetadataNotDownloaded.append(datasetPid)
                    dataverseJsonExportSaved = False
                    
                newRow = pd.Series([datasetPid, dataverseJsonExportSaved], index=columnNames)
                dataverseJsonExportSavedDF = dataverseJsonExportSavedDF.append(newRow, ignore_index=True)

                # dataverseJsonExportSavedDF.set_index('persistent_id', inplace=True)

            print(f'\t\tDownloaded Dataverse JSON metadata of {dataverseJsonmMetadataDownloadedCount} of {datasetCount} datasets')

            if dataverseJsonMetadataNotDownloaded:
                print(f'\t\tThe Dataverse JSON metadata of the following {len(dataverseJsonMetadataNotDownloaded)} dataset(s) could not be downloaded:')
                dataverseJsonMetadataNotDownloadedString = list_to_string(dataverseJsonMetadataNotDownloaded)
                print(f'\t\t{dataverseJsonMetadataNotDownloadedString}')

        dataverseJsonExportSavedDF = dataverseJsonExportSavedDF.set_index('persistent_id')

        # Turn datasetPidsFile into a dataframe to join with dataverseJsonExportSavedDF
        datasetPidsFileDF = pd.read_csv(datasetPidsFile).set_index('persistent_id')

        mergedFileDF = pd.merge(dataverseJsonExportSavedDF, datasetPidsFileDF, left_index=True, right_index=True).reset_index()

        mergedFile = installationDirectory + '/' + f'dataset_pids_{installationName}_merged_file.csv'
        columnOrderList = [
            'persistent_id', 'persistent_url', 'dataverse_name', 'dataverse_alias',
            'dataverse_json_export_saved']
        mergedFileDF = mergedFileDF[columnOrderList]
        mergedFileDF.to_csv(datasetPidsFile, index=False)

    installationProgressCount += 1

        # Draft code for getting metadata from other metadata exports

        #     exportFormat= 'schema.org'
        #     getschemaorgApiStatus = get_metadata_export_api_status(installationUrl, exportFormat=exportFormat, testDatasetPid)
        #     if getschemaorgApiStatus == 'OK':
        #         schemaorgMetadataDirectory = installationDirectory + '/' + 'schema_org_metadata' + f'_{currentTime}'
        #         os.mkdir(schemaorgMetadataDirectory)

        #         for row in csvDictReader:
        #             datasetPid = row['persistent_id'].rstrip()
        #             metadata = get_dataset_metadata_export(installationUrl, datasetPid, exportFormat, header=headers)
        #             # If metadata wasn't retrieved...
        #             if metadata != 'ERROR':
        #                 # Write to the datasetPidsFile, in the column for that export, that the metadata dataset was retrieved

        #                 # Create variable for file name and path for the dataset's metadata export
        #                 # Save metadata to the file in the directory

        #             # If metadata isn't retrieved...
        #             elif metadata == 'ERROR':
        #                 # Write to the datasetPidsFile, in the column for that export, that the metadata wasn't retrieved

        #     exportFormat = 'OAI_ORE'
        #     getOAI_OREApiUrl = get_metadata_export_api_status(installationUrl, exportFormat=exportFormat, testDatasetPid)
        #     if getOAI_OREApiUrl == 'OK':
        #         OAI_OREMetadataDirectory = installationDirectory + '/' + 'OAI_ORE_metadata' + f'_{currentTime}'
        #         os.mkdir(OAI_OREMetadataDirectory)

        #     exportFormat = 'ddi'
        #     getddiApiUrl = get_metadata_export_api_status(installationUrl, exportFormat=exportFormat, testDatasetPid)
        #     if getddiApiUrl == 'OK':
        #         ddiMetadataDirectory = installationDirectory + '/' + 'ddi_metadata' + f'_{currentTime}'
        #         os.mkdir(ddiMetadataDirectory)

        #     exportFormat = 'dcterms'
        #     getdctermsApiUrl = get_metadata_export_api_status(installationUrl, exportFormat=exportFormat, testDatasetPid)
        #     if getdctermsApiUrl == 'OK':
        #         dctermsMetadataDirectory = installationDirectory + '/' + 'dcterms_metadata' + f'_{currentTime}'
        #         os.mkdir(dctermsMetadataDirectory)

        #     exportFormat = 'oai_dc'
        #     getoai_dcApiUrl = get_metadata_export_api_status(installationUrl, exportFormat=exportFormat, testDatasetPid)
        #     if getoai_dcApiUrl == 'OK':
        #         oai_dcMetadataDirectory = installationDirectory + '/' + 'oai_dc_metadata' + f'_{currentTime}'
        #         os.mkdir(oai_dcMetadataDirectory)

        #     exportFormat = 'Datacite'
        #     getDataciteApiUrl = get_metadata_export_api_status(installationUrl, exportFormat=exportFormat, testDatasetPid)
        #     if getDataciteApiUrl == 'OK':
        #         DataciteMetadataDirectory = installationDirectory + '/' + 'Datacite_metadata' + f'_{currentTime}'
        #         os.mkdir(DataciteMetadataDirectory)

        #     exportFormat = 'oai_datacite'
        #     getOpenAIREApiUrl = get_metadata_export_api_status(installationUrl, exportFormat=exportFormat, testDatasetPid)
        #     if getOpenAIREApiUrl == 'OK':
        #         OpenAIREMetadataDirectory = installationDirectory + '/' + 'OpenAIRE_metadata' + f'_{currentTime}'
        #         os.mkdir(OpenAIREMetadataDirectory)

        # # Check if metadata for the dataset was retrieved
        # if data == 'ERROR':
        #     print('ERROR')
        # else:
        #     # Export data into a folder
        #     datasetPidForFile = datasetPid.replace(':', '_').replace('/', '_')
        #     if exportFormat in ['schema.org' , 'OAI_ORE']:
        #         metadataFilePath = '/Users/juliangautier/Desktop/' + f'{datasetPidForFile}.json'
        #         with open(metadataFilePath, mode='w') as f:
        #             f.write(json.dumps(data, indent=4))
        #     elif exportFormat not in ['schema.org' , 'OAI_ORE']:
        #         metadataFilePath = '/Users/juliangautier/Desktop/' + f'{datasetPidForFile}.xml'
        #         with open(metadataFilePath, mode='w') as f:
        #             f.write(data)
