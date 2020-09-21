# Download dataset metadata of as many known Dataverse-based repositories as possible

import json
import os
from pathlib import Path
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import time
from urllib.parse import urlparse

# Enter directory path for installation directories (if on a Windows machine, use forward slashes, which will be converted to back slashes)
base_directory = ''  # e.g. /Users/Owner/Desktop

# Enter a user agent and your email address. Some Dataverse-based repositories block requests from scripts.
# See https://www.whatismybrowser.com/detect/what-is-my-user-agent to get your user agent
user_agent = ''
email_address = ''

headers = {
    'User-Agent': user_agent,
    'From': email_address}

# Save current time to append it to CSV file
current_time = time.strftime('%Y.%m.%d_%H.%M.%S')

# Create the main directory that will store a directory for each repository
all_installations_metadata_directory = str(Path(base_directory + '/' + 'all_installation_metadata_%s' % (current_time)))
os.mkdir(all_installations_metadata_directory)


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


# Suppress warning message that appears when requests tries to get response from a website whose SSL
# cert requests can't verify because the request call isn't verifying certificate (verify=False)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Get JSON data from Dataverse installations map
print('Getting Dataverse installation data...')
map_data_url = 'https://raw.githubusercontent.com/IQSS/dataverse-installations/master/data/data.json'
response = requests.get(map_data_url, headers=headers)
mapdata = response.json()

count_of_installations = len(mapdata['installations'])

installation_errors = []

installation_progress_count = 1

for installation in mapdata['installations']:
    installation_name = installation['name']
    hostname = installation['hostname']
    repositoryURL = 'http://%s' % (hostname)
    print('\nChecking %s of %s repositories: %s' % (installation_progress_count, count_of_installations, installation_name))

    # Get status code of repository website or report no response from website
    try:
        response = requests.get(repositoryURL, headers=headers, timeout=20, verify=False)

        # Save final URL redirect to repositoryURL variable
        repositoryURL = response.url

        # Save only the base URL to the repositoryURL variable
        o = urlparse(repositoryURL)
        repositoryURL = o.scheme + '://' + o.netloc

        if (response.status_code == 200 or response.status_code == 301 or response.status_code == 302):
            installation_status = str(response.status_code)
    except Exception:
        installation_status = 'NA'
    print('\tInstallation status: %s' % (installation_status))

    # If there's a good response from the installation, check if Search API works by searching for repository's non-harvested datasets
    if installation_status != 'NA':
        search_api_url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=1&sort=date&order=desc' % (repositoryURL)
        search_api_url = search_api_url.replace('//api', '/api')
        search_api_status = checkapiendpoint(search_api_url)
    else:
        search_api_status = 'NA'

    # If Search API works, from Search API query results, get count of local (non-harvested) datasets
    if search_api_status == 'OK':
        response = requests.get(search_api_url, headers=headers, timeout=20, verify=False)
        search_api_data = response.json()
        dataset_count = search_api_data['data']['total_count']
    else:
        dataset_count = 'NA'
    print('\tSearch API status: %s' % (search_api_status))

    # Report if the repository has no published, non-harvested datasets
    if dataset_count == 0:
        print('\tRepository has 0 published, non-harvested datasets')

    # If there are local datasets, get the PID of a local dataset (used to check "Get dataset JSON" endpoint)
    if dataset_count != 'NA' and dataset_count > 0:
        test_dataset_pid = search_api_data['data']['items'][0]['global_id']
    else:
        test_dataset_pid = 'NA'

    # If a local dataset PID can be retreived, check if "Get dataset JSON" endpoint works
    if test_dataset_pid != 'NA':
        get_json_api_url = '%s/api/v1/datasets/:persistentId/?persistentId=%s' % (repositoryURL, test_dataset_pid)
        get_json_api_url = get_json_api_url.replace('//api', '/api')
        get_json_api_status = checkapiendpoint(get_json_api_url)
    else:
        get_json_api_status = 'NA'
    print('\t"Get dataset JSON" API status: %s' % (get_json_api_status))

    # If the "Get dataset JSON" endpoint works, download the repository's metadatablock JSON files, dataset PIDs, and dataset metadata

    if get_json_api_status == 'OK':

        # Save current time to append it to the repository's directory and text file
        current_time = time.strftime('%Y.%m.%d_%H.%M.%S')

        # Create directory for the repository
        repository_directory = all_installations_metadata_directory + '/' + installation_name.replace(' ', '_') + '_%s' % (current_time)
        os.mkdir(repository_directory)

        # Use the "Get Version" endpoint to get repository's Dataverse version (or set version as 'NA')
        get_installation_version_api_url = '%s/api/v1/info/version' % (repositoryURL)
        get_installation_version_api_url = get_installation_version_api_url.replace('//api', '/api')
        get_installation_version_api_status = checkapiendpoint(get_installation_version_api_url)

        if get_installation_version_api_status == 'OK':
            response = requests.get(get_installation_version_api_url, headers=headers, timeout=20, verify=False)
            get_installation_version_api_data = response.json()
            dataverse_version = get_installation_version_api_data['data']['version']
            dataverse_version = str(dataverse_version.lstrip('v'))
        else:
            dataverse_version = 'NA'

        print('\tDataverse version: %s' % (dataverse_version))

        # Create a directory for the repository's metadatablock files
        metadatablockFileDirectoryPath = repository_directory + '/' + 'metadatablocks_v%s' % (dataverse_version)
        os.mkdir(metadatablockFileDirectoryPath)

        # Download metadatablock JSON files

        # Get list of the repository's metadatablock names
        metadatablocks_api = '%s/api/v1/metadatablocks' % (repositoryURL)
        metadatablocks_api = metadatablocks_api.replace('//api', '/api')

        response = requests.get(metadatablocks_api, headers=headers, timeout=20, verify=False)
        metadatablock_data = response.json()

        metadatablock_names = []
        for i in metadatablock_data['data']:
            metadatablock_name = i['name']
            metadatablock_names.append(metadatablock_name)

        print('\tDownloading metadatablock JSON file(s) into metadatablocks folder')

        for metadatablock_name in metadatablock_names:
            metadatablock_api = '%s/%s' % (metadatablocks_api, metadatablock_name)
            response = requests.get(metadatablock_api, headers=headers, timeout=20, verify=False)
            metadata = response.json()

            # If the metadatablock has fields, download the metadatablock data into a JSON file
            if len(metadata['data']['fields']) > 0:

                metadatablock_file = str(Path(metadatablockFileDirectoryPath)) + '/' '%s_v%s.json' % (metadatablock_name, dataverse_version)

                with open(metadatablock_file, mode='w') as f:
                    f.write(json.dumps(response.json(), indent=4))

        # Use the Search API to get the repository's dataset PIDs and write them to a text file,
        # and use the "Get dataset JSON" endpoint to get those datasets' metadata

        # Create path and file name of text file for the dataset PIDs
        file_path = repository_directory + '/' + 'dataset_pids_%s_%s.txt' % (installation_name, current_time)

        # Use Search API to get repository's dataset PIDs and write them to a text file
        print('\tWriting %s dataset PIDs to text file:' % (dataset_count))

        # Initialization for paginating through Search API results and showing progress
        start = 0
        condition = True
        dataset_pid_count = 0

        # Create variable for storing count of misindexed datasets
        misindexed_datasets_count = 0

        with open(file_path, mode='w') as f1:
            while (condition):
                try:
                    per_page = 10
                    url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=%s&start=%s&sort=date&order=desc' % (repositoryURL, per_page, start)
                    response = requests.get(url, headers=headers, verify=False)
                    data = response.json()

                    # For each dataset, write the dataset PID to the text file
                    for i in data['data']['items']:
                        global_id = i['global_id']
                        f1.write('%s\n' % (global_id))
                        dataset_pid_count += 1
                        print('\t\t%s of %s' % (dataset_pid_count, dataset_count), end='\r', flush=True)

                    # Update variables to paginate through the search results
                    start = start + per_page

                # Print error message if misindexed datasets break the Search API call, and try the next page.
                # See https://github.com/IQSS/dataverse/issues/4225
                except Exception:
                    print('\t\tper_page=10 url broken. Checking per_page=1')
                    try:
                        per_page = 1
                        url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=%s&start=%s&sort=date&order=desc' % (repositoryURL, per_page, start)
                        response = requests.get(url, headers=headers, timeout=20, verify=False)
                        data = response.json()

                        # For each dataset, write the dataset PID to the text file
                        for i in data['data']['items']:
                            global_id = i['global_id']
                            f1.write('%s\n' % (global_id))
                            dataset_pid_count += 1
                            print('\t\t%s of %s' % (dataset_pid_count, dataset_count), end='\r', flush=True)

                            # Update variables to paginate through the search results
                            start = start + per_page

                    except Exception:
                        misindexed_datasets_count += 1
                        start = start + per_page

                # Stop paginating when there are no more results
                condition = start < dataset_count

            print('\n\t%s dataset PIDs written to text file' % (dataset_count))

        if misindexed_datasets_count:
            print('\n\n\tUnretrievable dataset PIDs due to misindexing: %s\n' % (misindexed_datasets_count))

        # Create directory for dataset JSON metadata
        json_metadata_directory = repository_directory + '/' + 'JSON_metadata' + '_%s' % (current_time)
        os.mkdir(json_metadata_directory)

        # For each dataset PID in text file, download dataset's JSON metadata
        print('\tDownloading JSON metadata to dataset_metadata folder:')

        # Initiate counts for progress indicator
        metadata_downloaded_count = 0
        metadata_not_downloaded = []

        dataset_pids = open(file_path)

        # For each dataset persistent identifier in the txt file, download the dataset's Dataverse JSON file into the metadata folder
        for dataset_pid in dataset_pids:

            # Remove any trailing spaces from pid
            dataset_pid = dataset_pid.rstrip()

            # Get the metadata of each version of the dataset
            try:
                latest_version_url = '%s/api/datasets/:persistentId?persistentId=%s' % (repositoryURL, dataset_pid)
                response = requests.get(latest_version_url, headers=headers, timeout=20, verify=False)
                latest_version_metadata = response.json()
                if latest_version_metadata['status'] == 'OK':
                    persistentUrl = latest_version_metadata['data']['persistentUrl']
                    publisher = latest_version_metadata['data']['publisher']
                    publicationDate = latest_version_metadata['data']['publicationDate']

                    all_version_url = '%s/api/datasets/:persistentId/versions?persistentId=%s' % (repositoryURL, dataset_pid)
                    response = requests.get(all_version_url, headers=headers, timeout=20, verify=False)
                    all_versions_metadata = response.json()

                    for dataset_version in all_versions_metadata['data']:
                        dataset_version = {
                            'status': latest_version_metadata['status'],
                            'data': {
                                'persistentUrl': persistentUrl,
                                'publisher': publisher,
                                'publicationDate': publicationDate,
                                'datasetVersion': dataset_version}}

                        majorversion = str(dataset_version['data']['datasetVersion']['versionNumber'])
                        minorversion = str(dataset_version['data']['datasetVersion']['versionMinorNumber'])
                        version_number = majorversion + '.' + minorversion

                        metadata_file = json_metadata_directory + '/' + '%s_v%s.json' % (dataset_pid.replace(':', '_').replace('/', '_'), version_number)

                        # Write the JSON to the new file
                        with open(metadata_file, mode='w') as f2:
                            f2.write(json.dumps(dataset_version, indent=4))

                # Increase count variable to track progress
                metadata_downloaded_count += 1

                # Print progress
                print('\t\tDownloaded %s of %s JSON files' % (metadata_downloaded_count, dataset_count), end='\r', flush=True)

            except Exception:
                metadata_not_downloaded.append(dataset_pid)

        print('\t\tDownloaded %s of %s JSON files' % (metadata_downloaded_count, dataset_count))

        if metadata_not_downloaded:
            print('The metadata of the following %s dataset(s) could not be downloaded:' % (len(metadata_not_downloaded)))
            print(metadata_not_downloaded)

    installation_progress_count += 1
