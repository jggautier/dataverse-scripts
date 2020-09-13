# Python script for downloading the Dataverse JSON metadata files of given list of datasets PIDs
# and the repository's metadatablock JSON

import csv
import json
import os
from pathlib import Path
from pyDataverse.api import Api
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
	dataset_pids = filedialog.askopenfilename(filetypes=[('Text files', '*.txt')])

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

    metadatablockFileDirectoryPath
    metadatablock_file = str(Path(metadatablockFileDirectoryPath)) + '/' '%s_%s.json' % (metadatablock_name, current_time)

    with open(metadatablock_file, mode='w') as f:
        f.write(json.dumps(response.json(), indent=4))

    sys.stdout.write('.')
    sys.stdout.flush()

print('\nFinished downloading %s metadatablock JSON file(s)' % (len(metadatablock_names)))

# Download dataset JSON metadata
print('Downloading JSON metadata to dataset_metadata folder:')

# Initiate count for terminal progress indicator
count = 0

# Save number of items in the dataset_pids txt file in "total" variable
total = len(open(dataset_pids).readlines())

dataset_pids = open(dataset_pids)

# Use pyDataverse to establish connection with server
api = Api(repositoryURL)

# For each dataset persistent identifier in the txt file, download the dataset's Dataverse JSON file into the metadata folder
for pid in dataset_pids:

	# Remove any trailing spaces from pid
	pid = pid.rstrip()

	# Use the pid as the file name, replacing the colon and slashes with underscores
	metadata_file = '%s.json' % (pid.replace(':', '_').replace('/', '_'))

	# Use Native API endpoint for getting JSON metadata of draft datasets if api key is provided
	# if apikey:
		# url = '%s/api/datasets/:persistentId?persistentId=%s&key=%s' %(server, pid, api)

		# response = urllib.request.urlopen(url)
		# source = response.read()
		# data = json.loads(source)

		# Write the JSON to the new file
		# with open(os.path.join(metadataFileDirectoryPath, filename), mode='w') as f:
		# 	json.dump(data, f, indent=4, sort_keys=True)

		# count += 1

		# Print progress
		# print('Downloaded %s of %s JSON files' %(count, total), end='\r', flush=True)

	# else:

	# Use pyDataverse to get the metadata of the dataset
	response = api.get_dataset(pid)

	# Write the JSON to the new file
	with open(os.path.join(metadataFileDirectoryPath, metadata_file), mode='w') as f:
		f.write(json.dumps(response.json(), indent=4))

	# Increase count variable to track progress
	count += 1

	# Print progress
	print('Downloaded %s of %s JSON files' % (count, total), end='\r', flush=True)

print('Downloaded %s of %s JSON files' % (count, total))
