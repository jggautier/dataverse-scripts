# Get the PIDs of datasets in a given dataverse (and optionally any dataverses in that dataverse).
# Includes deaccessioned datasets. Excludes harvested and linked datasets.

import csv
import glob
import json
import os
import requests
import sys
import time
from tkinter import filedialog
from tkinter import ttk
from tkinter import *
from urllib.parse import urlparse

####################################################################################

# Create GUI for getting user input

window = Tk()
window.title('Get dataset PIDs')
window.geometry('625x450')  # width x height


# Function called when Browse button is pressed
def retrieve_directory():
    global directory

    # Call the OS's file directory window and store selected object path as a global variable
    directory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + directory, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showChosenDirectory.grid(sticky='w', column=0, row=13)


# Function called when Start button is pressed
def retrieve_input():
    global dataverseUrl
    global apiKey
    global get_subdataverses

    # Record if user wants to search in subdataverses
    get_subdataverses = get_subdataverses.get()

    # Store what entered in the api key text box as a global variable
    apiKey = entry_apikey.get().rstrip()

    # Store what's entered in dataverseUrl text box as a global variable
    dataverseUrl = entry_dataverseUrl.get()

    # If user enters text in dataverseUrl text box, strip any white characters
    if dataverseUrl:
        dataverseUrl = str(dataverseUrl)
        dataverseUrl = dataverseUrl.strip()

        # If user also selected a directory, close the window
        if directory:
            window.destroy()

    # If no dataverseUrl is entered, display message that one is required
    else:
        print('A dataverse URL is required')
        label_dataverseUrlReqiured = Label(window, text='A dataverse URL is required.', foreground='red', anchor='w')
        label_dataverseUrlReqiured.grid(sticky='w', column=0, row=3)


# Create label for Dataverse URL field
label_dataverseUrl = Label(window, text='Dataverse URL:', anchor='w')
label_dataverseUrl.grid(sticky='w', column=0, row=0)

# Create Dataverse URL field
dataverseUrl = str()
entry_dataverseUrl = Entry(window, width=50, textvariable=dataverseUrl)
entry_dataverseUrl.grid(sticky='w', column=0, row=1, pady=2)
entry_dataverseUrl.insert(0, 'https://demo.dataverse.org/')

# Create help text for Dataverse URL field
label_dataverseUrlHelpText = Label(window, text='Example: https://demo.dataverse.org or https://demo.dataverse.org/dataverse/dataversealias', foreground='grey', anchor='w')
label_dataverseUrlHelpText.grid(sticky='w', column=0, row=2)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(4, minsize=25)

# Create "Include subdataverses" checkbox
get_subdataverses = IntVar()
c = Checkbutton(window, text="Include subdataverses", variable=get_subdataverses).grid(sticky='w', column=0, row=5)

# Create help text for "Include subdataverses" checkbox
label_apikeyHelpText = Label(
    window,
    text='If the URL of the "Root" Dataverse collection is entered, all datasets in the repository (in all subdataverses) will be found',
    foreground='grey', anchor='w', wraplength=500, justify='left')
label_apikeyHelpText.grid(sticky='w', column=0, row=6)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(7, minsize=25)

# Create label for API key field
label_apikey = Label(window, text='API key:', anchor='w')
label_apikey.grid(sticky='w', column=0, row=8)

# Create API key field
apiKey = str()
entry_apikey = Entry(window, width=50, textvariable=apiKey)
entry_apikey.grid(sticky='w', column=0, row=9, pady=2)

# Create help text for API key field
label_apikeyHelpText = Label(window, text='If no API is entered, only published datasets will be found', foreground='grey', anchor='w')
label_apikeyHelpText.grid(sticky='w', column=0, row=10)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(11, minsize=25)

# Create label for Browse directory button
label_browseDirectory = Label(window, text='Choose folder to store CSV file with info of dataset PIDs:', anchor='w')
label_browseDirectory.grid(sticky='w', column=0, row=12, pady=2)

# Create Browse directory button
button_browseDirectory = ttk.Button(window, text='Browse', command=lambda: retrieve_directory())
button_browseDirectory.grid(sticky='w', column=0, row=13)

# Create start button
button_Submit = ttk.Button(window, text='Start', command=lambda: retrieve_input())
button_Submit.grid(sticky='w', column=0, row=15, pady=40)

# Keep window open until it's closed
mainloop()

# Save current time to append it to main folder name
current_time = time.strftime('%Y.%m.%d_%H.%M.%S')

# Parse dataverseUrl to get installation name and alias
parsed = urlparse(dataverseUrl)
installationUrl = parsed.scheme + '://' + parsed.netloc
# alias = parsed.path.split('/')[2]

try:
    alias = parsed.path.split('/')[2]
except IndexError:
    alias = ''

# Get alias of the root dataverse (assumming the root dataverse's ID is 1, which isn't the case with UVA Dataverse)
url = f'%s/api/dataverses/1' % (installationUrl)
response = requests.get(url)
dataverse_data = response.json()
root_alias = dataverse_data['data']['alias']
installation_name = dataverse_data['data']['name']

####################################################################################

# If user provides no alias or the alias is the repository's root alias,
# use Search API to find PIDs of all datasets in repository

if not alias or alias == root_alias:

    # Create CSV file
    csv_file = 'dataset_pids_%s_%s.csv' % (installation_name.replace(' ', '_'), current_time)
    csv_file_path = os.path.join(directory, csv_file)

    with open(csv_file_path, mode='w', newline='') as f:
        f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        f.writerow(['persistent_id', 'persistentUrl', 'dataverse_name', 'dataverse_alias', 'publication_date'])

    # Report count of datasets
    if apiKey:
        url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=1&start=0&sort=date&order=desc&key=%s' % (installationUrl, apiKey)
        response = requests.get(url)
        data = response.json()
        total = data['data']['total_count']
        print('\nSaving %s dataset PIDs\n(Search API returns the draft and published version of a dataset. List will be de-duplicated at the end):' % (total))
    else:
        url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=1&start=0&sort=date&order=desc' % (installationUrl)
        response = requests.get(url)
        data = response.json()
        total = data['data']['total_count']
        print('\nSaving %s dataset PIDs:' % (total))

    # Initialization for paginating through Search API results and showing progress
    start = 0
    condition = True
    count = 0

    # Create variable for storing count of misindexed datasets
    misindexed_datasets_count = 0

    while condition:
        try:
            per_page = 10
            if apiKey:
                url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=%s&start=%s&sort=date&order=desc&key=%s' % (installationUrl, per_page, start, apiKey)
            else:
                url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=%s&start=%s&sort=date&order=desc' % (installationUrl, per_page, start)

            response = requests.get(url)
            data = response.json()

            # For each item object...
            for i in data['data']['items']:
                persistent_id = i['global_id']
                persistent_url = i['url']
                dataverse_name = i['name_of_dataverse']
                dataverse_alias = i['identifier_of_dataverse']
                publicationDate = i.get('published_at', 'UNPUBLISHED')

                with open(csv_file_path, mode='a', encoding='utf-8', newline='') as open_csv_file:
                    open_csv_file = csv.writer(open_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                    # Create new row with dataset and file info
                    open_csv_file.writerow([persistent_id, persistent_url, dataverse_name, dataverse_alias, publicationDate])

                    count += 1
                    print('%s of %s' % (count, total), end='\r', flush=True)

            # Update variables to paginate through the search results
            start = start + per_page

        # Print error message if misindexed datasets break the Search API call, and try the next page. (See https://github.com/IQSS/dataverse/issues/4225)
        except urllib.error.URLError:
            try:
                per_page = 1
                if apiKey:
                    url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=%s&start=%s&sort=date&order=desc&key=%s' % (installationUrl, per_page, start, apiKey)
                else:
                    url = '%s/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=%s&start=%s&sort=date&order=desc' % (installationUrl, per_page, start)

                response = requests.get(url)
                data = response.json()

                # For each item object...
                for i in data['data']['items']:
                    persistent_id = i['global_id']
                    persistent_url = i['url']
                    dataverse_name = i['name_of_dataverse']
                    dataverse_alias = i['identifier_of_dataverse']
                    publicationDate = i.get('published_at', 'unpublished')

                    with open(csv_file_path, mode='a', encoding='utf-8', newline='') as open_csv_file:
                        open_csv_file = csv.writer(open_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                        # Create new row with dataset and file info
                        open_csv_file.writerow([persistent_id, persistent_url, dataverse_name, dataverse_alias, publicationDate])

                        print('%s of %s' % (count, total), end='\r', flush=True)

                    # Update variables to paginate through the search results
                    start = start + per_page

            except urllib.error.URLError:
                misindexed_datasets_count += 1
                start = start + per_page

        # Stop paginating when there are no more results
        condition = start < total

    print('\nDataset PIDs written to the CSV file: %s' % (count))

    if misindexed_datasets_count:
        print('\n\nUnretrievable dataset PIDs due to misindexing: %s\n' % (misindexed_datasets_count))

####################################################################################

# If user provides an alias, and it isn't the root dataverses's alias, use "Get content" endpoints instead of Search API

else:
    csv_file = 'dataset_pids_%s_%s.csv' % (alias, current_time)
    csv_file_path = os.path.join(directory, csv_file)

    with open(csv_file_path, mode='w', newline='') as f:
        f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        f.writerow(['persistent_id', 'persistentUrl', 'dataverse_name', 'dataverse_alias', 'publication_date'])

    # Get ID of given dataverse alias
    if apiKey:
        url = '%s/api/dataverses/%s?key=%s' % (installationUrl, alias, apiKey)
    else:
        url = '%s/api/dataverses/%s' % (installationUrl, alias)

    response = requests.get(url)
    data = response.json()
    parent_dataverse_id = data['data']['id']

    # Create list and add ID of given dataverse
    dataverse_ids = [parent_dataverse_id]

    # If user wants datasets in subdataverses, search for and include IDs of subdataverses (excludes linked dataverses)

    # Get each subdataverse in the given dataverse
    if get_subdataverses == 1:
        print('\nGetting dataverse IDs in %s:' % (alias))

        for dataverse_id in dataverse_ids:

            sys.stdout.write('.')
            sys.stdout.flush()

            if apiKey:
                url = '%s/api/dataverses/%s/contents?key=%s' % (installationUrl, dataverse_id, apiKey)
            else:
                url = '%s/api/dataverses/%s/contents' % (installationUrl, dataverse_id)

            response = requests.get(url)
            data = response.json()

            for i in data['data']:
                if i['type'] == 'dataverse':
                    dataverse_id = i['id']
                    dataverse_ids.extend([dataverse_id])

        print('\n\nFound 1 dataverse and %s subdataverses' % (len(dataverse_ids) - 1))

    # For each dataverse in the list, add the PIDs of all datasets to a CSV file - excludes linked and harvested datasets

    print('\nWriting dataset IDs to %s:' % (csv_file_path))

    count = 0

    with open(csv_file_path, mode='a', encoding='utf-8', newline='') as open_csv_file:
        open_csv_file = csv.writer(open_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for dataverse_id in dataverse_ids:

            # Get name of dataverse
            if apiKey:
                url = '%s/api/dataverses/%s?key=%s' % (installationUrl, dataverse_id, apiKey)
            else:
                url = '%s/api/dataverses/%s' % (installationUrl, dataverse_id)
            response = requests.get(url, timeout=10)
            data = response.json()
            dataverse_name = data['data']['name']
            dataverse_alias = data['data']['alias']

            # Get content of dataverse
            if apiKey:
                url = '%s/api/dataverses/%s/contents?key=%s' % (installationUrl, dataverse_id, apiKey)
            else:
                url = '%s/api/dataverses/%s/contents' % (installationUrl, dataverse_id)

            response = requests.get(url)
            data = response.json()

            for i in data['data']:
                if i['type'] == 'dataset':
                    protocol = i['protocol']
                    authority = i['authority']
                    identifier = i['identifier']
                    persistent_id = '%s:%s/%s' % (protocol, authority, identifier)
                    persistent_url = i['persistentUrl']
                    publicationDate = i.get('publicationDate', 'unpublished')

                    count += 1

                    # Create new line with dataset PID
                    open_csv_file.writerow([persistent_id, persistent_url, dataverse_name, dataverse_alias, publicationDate])

                    # As a progress indicator, print a dot each time a row is written
                    sys.stdout.write('.')
                    sys.stdout.flush()

    print('\n\nDataset PIDs written to the CSV file: %s' % (count))
