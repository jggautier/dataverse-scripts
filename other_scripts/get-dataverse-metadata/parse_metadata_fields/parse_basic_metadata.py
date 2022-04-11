# For each dataset listed in dataset_pids.txt, get the basic metadata that lives outside of the metadata blocks

import csv
import json
import glob
import os
from pathlib import Path
import re
import sys
from tkinter import filedialog
from tkinter import ttk
from tkinter import *

# Create GUI for getting user input

# Create, title and size the window
window = Tk()
window.title('Get basic dataset metadata')
window.geometry('550x500')  # width x height


def get_canonical_pid(pidOrUrl):

    # If entered dataset PID is the dataset page URL, get canonical PID
    if pidOrUrl.startswith('http') and 'persistentId=' in pidOrUrl:
        canonicalPid = pidOrUrl.split('persistentId=')[1]
        canonicalPid = canonicalPid.split('&version')[0]
        canonicalPid = canonicalPid.replace('%3A', ':').replace('%2F', ('/'))

    # If entered dataset PID is a DOI URL, get canonical PID
    elif pidOrUrl.startswith('http') and 'doi.' in pidOrUrl:
        canonicalPid = re.sub('http.*org\/', 'doi:', pidOrUrl)

    elif pidOrUrl.startswith('doi:') and '/' in pidOrUrl:
        canonicalPid = pidOrUrl

    # If entered dataset PID is a Handle URL, get canonical PID
    elif pidOrUrl.startswith('http') and 'hdl.' in pidOrUrl:
        canonicalPid = re.sub('http.*net\/', 'hdl:', pidOrUrl)

    elif pidOrUrl.startswith('hdl:') and '/' in pidOrUrl:
        canonicalPid = pidOrUrl

    return canonicalPid


# Function called when user presses button to browse for JSON files directory
def retrieve_jsondirectory():
    global jsonDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    jsonDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + jsonDirectory, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showChosenDirectory.grid(sticky='w', column=0, row=2)


# Function called when user presses button to browse for CSV files directory
def retrieve_csvdirectory():
    global csvDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    csvDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + csvDirectory, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showChosenDirectory.grid(sticky='w', column=0, row=6)


# Function called when Start button is pressed
def start():
    window.destroy()


# Create label for button to browse for directory containing JSON files
label_getJSONFiles = Label(window, text='Choose folder containing the JSON files:', anchor='w')
label_getJSONFiles.grid(sticky='w', column=0, row=0, pady=2)

# Create button to browse for directory containing JSON files
button_getJSONFiles = ttk.Button(window, text='Browse', command=lambda: retrieve_jsondirectory())
button_getJSONFiles.grid(sticky='w', column=0, row=1)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(3, minsize=25)

# Create label for button to browse for directory to add csv files in
label_tablesDirectory = Label(window, text='Choose folder to store the csv file:', anchor='w')
label_tablesDirectory.grid(sticky='w', column=0, row=4, pady=2)

# Create button to browse for directory containing JSON files
button_tablesDirectory = ttk.Button(window, text='Browse', command=lambda: retrieve_csvdirectory())
button_tablesDirectory.grid(sticky='w', column=0, row=5)

# Create start button
button_Start = ttk.Button(window, text='Start', command=lambda: start())
button_Start.grid(sticky='w', column=0, row=7, pady=40)

# Keep window open until it's closed
mainloop()


def improved_get(_dict, path, default=None):
    for key in path.split('.'):
        try:
            _dict = _dict[key]
        except KeyError:
            return default
    return str(_dict)


# Add path of csv file to filename variable
filename = os.path.join(csvDirectory, 'basic_metadata.csv')

print('Creating CSV file')

with open(filename, mode='w', newline='') as metadatafile:
    metadatafile = csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Create header row
    metadatafile.writerow([
            'dataset_pid', 'dataset_pid_url', 'dataset_version_number', 'dataset_publication_date', 
            'dataset_version_create_time', 'dataset_version_state', 'publisher'])

print('Getting metadata:')
error_files = []
fileCount = 0
fileCountTotal = len(glob.glob(os.path.join(jsonDirectory, '*.json')))

# For each JSON file in a folder
for file in glob.glob(os.path.join(jsonDirectory, '*.json')):
    fileCount += 1
    print(f'Getting metadata from {fileCount} of {fileCountTotal} files', end='\r', flush=True)
    # Open each file in read mode
    with open(file, 'r') as f1:
        # Copy content to datasetMetadata variable
        datasetMetadata = f1.read()
        # Load content in variable as a json object
        datasetMetadata = json.loads(datasetMetadata)

        # Check if JSON file has "data" key
        if datasetMetadata['status'] == 'OK':
            # datasetVersionId = datasetMetadata['data']['datasetVersion']['id']

            # datasetPersistentId = improved_get(datasetMetadata, 'data.datasetVersion.datasetPersistentId')
            datasetPersistentUrl = datasetMetadata['data']['persistentUrl']
            datasetPersistentId = get_canonical_pid(datasetPersistentUrl)

            majorVersionNumber = improved_get(datasetMetadata, 'data.datasetVersion.versionNumber')
            minorVersionNumber = improved_get(datasetMetadata, 'data.datasetVersion.versionMinorNumber')
            datasetVersionNumber = f'{majorVersionNumber}.{minorVersionNumber}'

            datasetVersionCreateTime = datasetMetadata['data']['datasetVersion']['createTime']
            datasetVersionState = datasetMetadata['data']['datasetVersion']['versionState']
            datasetPublicationDate = datasetMetadata['data']['publicationDate']
            publisher = datasetMetadata['data']['publisher']

            # Write fields to the csv file
            with open(filename, mode='a', newline='') as metadatafile:

                # Convert all characters to utf-8
                def to_utf8(lst):
                    return [unicode(elem).encode('utf-8') for elem in lst]

                metadatafile = csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                # Write new row
                metadatafile.writerow([
                    datasetPersistentId, datasetPersistentUrl, datasetVersionNumber, datasetPublicationDate,
                    datasetVersionCreateTime, datasetVersionState, publisher])

        # If JSON file doens't have "data" key, add file to list of error_files
        else:
            error_files.append(Path(file).name)
print(f'Finished getting metadata from {fileCount} of {fileCountTotal} files')

if error_files:
    print(f'\nThe following files may not have metadata:{error_files}')
