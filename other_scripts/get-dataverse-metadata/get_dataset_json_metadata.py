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
import sys

sys.path.append('/Users/juliangautier/dataverse-scripts/dataverse_repository_curation_assistant')
from dataverse_repository_curation_assistant_functions import *

# Create GUI for getting user input
window = Tk()
window.title('Get dataset metadata')
window.geometry('650x600')  # width x height

# Create label for Dataverse repository URL
labelInstallationUrl = Label(window, text='Enter Dataverse repository URL:', anchor='w')
labelInstallationUrl.grid(sticky='w', column=0, row=0)

# Create Dataverse repository URL text box
installationUrl = str()
entryInstallationUrl = Entry(window, width=50, textvariable=installationUrl)
entryInstallationUrl.grid(sticky='w', column=0, row=1, pady=2)

# Create help text for server name field
labelDataverseUrlHelpText = Label(window, text='Example: https://demo.dataverse.org/', foreground='grey', anchor='w')
labelDataverseUrlHelpText.grid(sticky='w', column=0, row=2)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(3, minsize=25)

# Create label for API key field
labelApikey = Label(window, text='API token/key:', anchor='w')
labelApikey.grid(sticky='w', column=0, row=4)

# Create API key field
apiKey = str()
entryApiKey = Entry(window, width=50, textvariable=apiKey)
entryApiKey.grid(sticky='w', column=0, row=5, pady=2)

# Create help text for API key field
labelApikeyHelpText = Label(window, text='If no API token/key is entered, only published metadata will be downloaded', foreground='grey', anchor='w')
labelApikeyHelpText.grid(sticky='w', column=0, row=6)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(7, minsize=25)

getAllVersionMetadata = IntVar()
Checkbutton(window, text="Get metadata of all dataset versions", variable=getAllVersionMetadata).grid(sticky='w', column=0, row=8)

# Create help text for all versions checkbox
labelAllVersionMetadataHelpText = Label(window, text='If unchecked, only metadata of latest dataset version will be downloaded', foreground='grey', anchor='w')
labelAllVersionMetadataHelpText.grid(sticky='w', column=0, row=9)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(10, minsize=25)

# Create label for Browse directory button
labelBrowseForFile = Label(window, text='Choose CSV or TXT file containing list of dataset PIDs:', anchor='w')
labelBrowseForFile.grid(sticky='w', column=0, row=11, pady=2)

# Create Browse directory button
buttonBrowseForFile = ttk.Button(window, text='Browse', command=lambda: retrieve_file())
buttonBrowseForFile.grid(sticky='w', column=0, row=12)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(14, minsize=25)

# Create label for Browse directory button
labelBrowseDirectory = Label(window, text='Choose folder to put the metadata files and metadatablock files folders into:', anchor='w')
labelBrowseDirectory.grid(sticky='w', column=0, row=15, pady=2)

# Create Browse directory button
buttonBrowseDirectory = ttk.Button(window, text='Browse', command=lambda: retrieve_directory())
buttonBrowseDirectory.grid(sticky='w', column=0, row=16)

# Create start button
buttonSubmit = ttk.Button(window, text='Start', command=lambda: retrieve_input())
buttonSubmit.grid(sticky='w', column=0, row=18, pady=40)


# Function called when Browse button is pressed for choosing text file with dataset PIDs
def retrieve_file():
    global datasetPidFile

    # Call the OS's file directory window and store selected object path as a global variable
    datasetPidFile = filedialog.askopenfilename(filetypes=[('Text files', '*.txt'), ('CSV files', '*.csv')])

    # Show user which file she chose
    labelShowChosenFile = Label(window, text='You chose: ' + datasetPidFile, anchor='w', foreground='green', wraplength=500, justify='left')
    labelShowChosenFile.grid(sticky='w', column=0, row=13)


# Function called when Browse button is pressed
def retrieve_directory():
    global metadataFileDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    metadataFileDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    labelShowChosenDirectory = Label(
        window,
        text='You chose: ' + metadataFileDirectory,
        anchor='w', foreground='green',
        wraplength=500, justify='left'
    )
    labelShowChosenDirectory.grid(sticky='w', column=0, row=17)


# Function called when Start button is pressed
def retrieve_input():
    global installationUrl
    global apiKey
    global getAllVersionMetadata

    # Record if user wants metadata from all dataset versions
    getAllVersionMetadata = getAllVersionMetadata.get()

    # Store what's entered in dataverseUrl text box as a global variable
    installationUrl = entryInstallationUrl.get()

    # Store what's entered in the API key text box as a global variable
    apiKey = entryApiKey.get().rstrip()
    window.destroy()


# Keep window open until it's closed
mainloop()

# Save current time to append it to main folder name
currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

# Use the "Get Version" endpoint to get repository's Dataverse version (or set version as 'NA')
getInstallationVersionApiUrl = f'%s/api/v1/info/version' % (installationUrl)
response = requests.get(getInstallationVersionApiUrl)
getInstallationVersionApiData = response.json()
dataverseVersion = getInstallationVersionApiData['data']['version']
dataverseVersion = str(dataverseVersion.lstrip('v'))

# Download metadatablock JSON files
# Create name for metadatablock files directory in main directory
metadatablockFileDirectoryPath = str(Path(metadataFileDirectory)) + '/' + f'metadatablocks_v{dataverseVersion}'
os.mkdir(metadatablockFileDirectoryPath)

# Get list of the repository's metadatablock names
metadatablocksApi = f'{installationUrl}/api/v1/metadatablocks'
metadatablocksApi = metadatablocksApi.replace('//api', '/api')

response = requests.get(metadatablocksApi)
data = response.json()

metadatablockNames = []
for i in data['data']:
    name = i['name']
    metadatablockNames.append(name)

metadatablockNamesCount = len(metadatablockNames)

print(f'Downloading {metadatablockNamesCount} metadatablock JSON file(s) into metadatablocks folder:')

for metadatablockName in metadatablockNames:
    metadatablockApi = f'{metadatablocksApi}/{metadatablockName}'
    response = requests.get(metadatablockApi)

    metadatablockFile = str(Path(metadatablockFileDirectoryPath)) + '/' f'{metadatablockName}_v{dataverseVersion}.json'

    with open(metadatablockFile, mode='w') as f:
        f.write(json.dumps(response.json(), indent=4))

    sys.stdout.write('.')
    sys.stdout.flush()

print(f'\nFinished downloading {metadatablockNamesCount} metadatablock JSON file(s)')

# Create directory for metadata exports with current time
metadataFileDirectoryPath = str(Path(metadataFileDirectory)) + '/' + f'JSON_metadata_{currentTime}'
os.mkdir(metadataFileDirectoryPath)

if getAllVersionMetadata != 1:
    print('\nDownloading JSON metadata of latest published dataset versions to dataset_metadata folder:')
elif getAllVersionMetadata == 1:
    print('\nDownloading JSON metadata of all published dataset versions to dataset_metadata folder:')

# Initiate count for terminal progress indicator
count = 0

datasetPids = []
if '.csv' in datasetPidFile:
    with open(datasetPidFile, mode='r', encoding='utf-8') as f:
        csvDictReader = DictReader(f, delimiter=',')
        for row in csvDictReader:
            datasetPids.append(row['persistent_id'].rstrip())

elif '.txt' in datasetPidFile:
    datasetPidFile = open(datasetPidFile)
    for datasetPid in datasetPidFile:

        # Remove any trailing spaces from datasetPid
        datasetPids.append(datasetPid.rstrip())

downloadStatusFilePath = str(Path(metadataFileDirectory)) + '/' + f'download_status_{currentTime}.csv'

if getAllVersionMetadata != 1:
    save_dataset_exports(
        directoryPath=metadataFileDirectoryPath,
        downloadStatusFilePath=downloadStatusFilePath,
        installationUrl=installationUrl, datasetPidList=datasetPids, 
        exportFormat='dataverse_json', verify=False, allVersions=False, 
        header={}, apiKey=apiKey)

elif getAllVersionMetadata == 1:
    save_dataset_exports(
        directoryPath=metadataFileDirectoryPath,
        downloadStatusFilePath=downloadStatusFilePath,
        installationUrl=installationUrl, datasetPidList=datasetPids, 
        exportFormat='dataverse_json', timeout=60,
        verify=False, allVersions=True, 
        header={}, apiKey=apiKey)

