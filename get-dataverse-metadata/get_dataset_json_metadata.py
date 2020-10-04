# Python script for downloading the Dataverse JSON metadata files of given list of datasets PIDs
# and the repository's metadatablock JSON

import csv
from csv import DictReader
import json
import os
from pathlib import Path
import requests
import time
from tkinter import *
from tkinter import filedialog
from tkinter import ttk

# Create GUI for getting user input
window = Tk()
window.title('Get dataset metadata')
window.geometry('650x400')  # width x height

# Create label for Dataverse repository URL
label_repositoryURL = Label(window, text='Enter Dataverse repository URL:', anchor='w')
label_repositoryURL.grid(sticky='w', column=0, row=0)

# Create Dataverse repository URL text box
repositoryURL = str()
entry_repositoryURL = Entry(window, width=50, textvariable=repositoryURL)
entry_repositoryURL.grid(sticky='w', column=0, row=1, pady=2)

# Create help text for server name field
label_dataverseUrlHelpText = Label(window, text='Example: https://demo.dataverse.org/', foreground='grey', anchor='w')
label_dataverseUrlHelpText.grid(sticky='w', column=0, row=2)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(3, minsize=25)

# Create label for Browse directory button
label_browseForFile = Label(window, text='Choose txt file contain list of dataset PIDs:', anchor='w')
label_browseForFile.grid(sticky='w', column=0, row=4, pady=2)

# Create Browse directory button
button_browseForFile = ttk.Button(window, text='Browse', command=lambda: retrieve_file())
button_browseForFile.grid(sticky='w', column=0, row=5)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(7, minsize=25)

# Create label for Browse directory button
label_browseDirectory = Label(window, text='Choose folder to put the metadata files and metadatablock files folders into:', anchor='w')
label_browseDirectory.grid(sticky='w', column=0, row=8, pady=2)

# Create Browse directory button
button_browseDirectory = ttk.Button(window, text='Browse', command=lambda: retrieve_directory())
button_browseDirectory.grid(sticky='w', column=0, row=9)

# Create start button
button_Submit = ttk.Button(window, text='Start', command=lambda: retrieve_input())
button_Submit.grid(sticky='w', column=0, row=11, pady=40)


# Function called when Browse button is pressed for choosing text file with dataset PIDs
def retrieve_file():
    global dataset_pids

    # Call the OS's file directory window and store selected object path as a global variable
    dataset_pids = filedialog.askopenfilename(filetypes=[('Text files', '*.txt'), ('CSV files', '*.csv')])

    # Show user which file she chose
    label_showChosenFile = Label(window, text='You chose: ' + dataset_pids, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showChosenFile.grid(sticky='w', column=0, row=6)


# Function called when Browse button is pressed
def retrieve_directory():
    global metadataFileDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    metadataFileDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + metadataFileDirectory, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showChosenDirectory.grid(sticky='w', column=0, row=10)


# Function called when Start button is pressed
def retrieve_input():
    global repositoryURL

    # Store what's entered in dataverseUrl text box as a global variable
    repositoryURL = entry_repositoryURL.get()

    window.destroy()


# Keep window open until it's closed
mainloop()

# Save current time to append it to main folder name
current_time = time.strftime('%Y.%m.%d_%H.%M.%S')

# Use the "Get Version" endpoint to get repository's Dataverse version (or set version as 'NA')
get_installation_version_api_url = '%s/api/v1/info/version' % (repositoryURL)
response = requests.get(get_installation_version_api_url)
get_installation_version_api_data = response.json()
dataverse_version = get_installation_version_api_data['data']['version']
dataverse_version = str(dataverse_version.lstrip('v'))

# Save directory with dataverse alias and current time
metadataFileDirectoryPath = str(Path(metadataFileDirectory)) + '/' + 'JSON_metadata_%s' % (current_time)

metadatablockFileDirectoryPath = str(Path(metadataFileDirectory)) + '/' + 'metadatablocks_v%s' % (dataverse_version)

# Create dataset metadata and metadatablock directories
os.mkdir(metadataFileDirectoryPath)
os.mkdir(metadatablockFileDirectoryPath)

# Download metadatablock JSON files
# Get list of the repository's metadatablock names
metadatablocks_api = '%s/api/v1/metadatablocks' % (repositoryURL)
metadatablocks_api = metadatablocks_api.replace('//api', '/api')

response = requests.get(metadatablocks_api)
data = response.json()

metadatablock_names = []
for i in data['data']:
    name = i['name']
    metadatablock_names.append(name)

print('Downloading %s metadatablock JSON file(s) into metadatablocks folder:' % ((len(metadatablock_names))))

for metadatablock_name in metadatablock_names:
    metadatablock_api = '%s/%s' % (metadatablocks_api, metadatablock_name)
    response = requests.get(metadatablock_api)

    metadatablock_file = str(Path(metadatablockFileDirectoryPath)) + '/' '%s_v%s.json' % (metadatablock_name, dataverse_version)

    with open(metadatablock_file, mode='w') as f:
        f.write(json.dumps(response.json(), indent=4))

    sys.stdout.write('.')
    sys.stdout.flush()

print('\nFinished downloading %s metadatablock JSON file(s)' % (len(metadatablock_names)))

# Download dataset JSON metadata
print('\nDownloading JSON metadata of all published dataset versions to dataset_metadata folder:')

# Initiate count for terminal progress indicator
count = 0

# Figure out if given file with dataset_pids is a txt file or csv file
file_name = os.path.basename(dataset_pids)

if '.txt' in file_name:

    # Save number of items in the dataset_pids txt file in "total" variable
    total = len(open(dataset_pids).readlines())

    dataset_pids = open(dataset_pids)

    # For each dataset persistent identifier in the txt file, download the dataset's Dataverse JSON file into the metadata folder
    for dataset_pid in dataset_pids:

        # Remove any trailing spaces from dataset_pid
        dataset_pid = dataset_pid.rstrip()

        try:
            latest_version_url = '%s/api/datasets/:persistentId?persistentId=%s' % (repositoryURL, dataset_pid)
            response = requests.get(latest_version_url)
            latest_version_metadata = response.json()

            if latest_version_metadata['status'] == 'OK':
                persistentUrl = latest_version_metadata['data']['persistentUrl']
                publisher = latest_version_metadata['data']['publisher']
                publicationDate = latest_version_metadata['data']['publicationDate']

                all_version_url = '%s/api/datasets/:persistentId/versions?persistentId=%s' % (repositoryURL, dataset_pid)
                response = requests.get(all_version_url)
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

                    metadata_file = '%s_v%s.json' % (dataset_pid.replace(':', '_').replace('/', '_'), version_number)

                    with open(os.path.join(metadataFileDirectoryPath, metadata_file), mode='w') as f:
                        f.write(json.dumps(dataset_version, indent=4))

            # Increase count variable to track progress
            count += 1

            # Print progress
            print('%s of %s datasets' % (count, total), end='\r', flush=True)

        except Exception:
            print('Could not download JSON metadata of %s' % (dataset_pid))

else:
    if '.csv' in file_name:
        with open(dataset_pids, mode='r', encoding='utf-8') as f:
            total = len(f.readlines()) - 1
        with open(dataset_pids, mode='r', encoding='utf-8') as f:
            csv_dict_reader = DictReader(f, delimiter=',')
            # total = 0
            for row in csv_dict_reader:
                # total += 1
                dataset_pid = row['persistent_id'].rstrip()
                try:
                    latest_version_url = '%s/api/datasets/:persistentId?persistentId=%s' % (repositoryURL, dataset_pid)
                    response = requests.get(latest_version_url)
                    latest_version_metadata = response.json()

                    if latest_version_metadata['status'] == 'OK':
                        persistentUrl = latest_version_metadata['data']['persistentUrl']
                        publisher = latest_version_metadata['data']['publisher']
                        publicationDate = latest_version_metadata['data']['publicationDate']

                        all_version_url = '%s/api/datasets/:persistentId/versions?persistentId=%s' % (repositoryURL, dataset_pid)
                        response = requests.get(all_version_url)
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

                            metadata_file = '%s_v%s.json' % (dataset_pid.replace(':', '_').replace('/', '_'), version_number)

                            with open(os.path.join(metadataFileDirectoryPath, metadata_file), mode='w') as f:
                                f.write(json.dumps(dataset_version, indent=4))

                    # Increase count variable to track progress
                    count += 1

                    # Print progress
                    print('%s of %s datasets' % (count, total), end='\r', flush=True)
                    # print('%s' % (count), end='\r', flush=True)

                except Exception:
                    print('Could not download JSON metadata of %s' % (dataset_pid))
