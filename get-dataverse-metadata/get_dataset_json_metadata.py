# Python script for downloading the Dataverse JSON metadata files of given list of datasets PIDs

'''
To-do

	- When getting dataset metadata with pyDataverse, use try/except where the exception is that the json metadata can't be retrived,
	because it's not a valid DOI or is an unpublished dataset, or it has no "latestVersion" section, usually because all of the dataset's 
	versions are deaccessioned.

	When the exception is met, print in the terminal or print to a text file a list of given PIDs whose dataverse-json files can't be retrieved.
		Code:
			api=Api(server)
			pid=''
			resp=api.get_dataset(pid)

			# If there's an error, continue to next dataset
			elif resp['data']['latestVersion']['versionState']:
				print('Dataset with Persistent ID %s not found, is unpublished or is deaccessioned.' %(pid))
			elif ... page can't be reached or status is "ERROR"
				print('Dataset with Persistent ID %s not found, is unpublished or is deaccessioned.' %(pid))
			else:
				print('Dataset with Persistent ID %s not found, is unpublished or is deaccessioned.' %(pid))

	- Open issue about how Dataverse should export metadata of deaccesioned datasets. See what this returns:
	https://dataverse.harvard.edu/api/datasets/export?exporter=dataverse_json&persistentId=doi:10.7910/DVN/B74GN1. (Also does not work when given an API key
	of an account with permissions on the dataset, like a superuser account.)
	Add that pyDataverse, when passed the DOI of a dataset whose versions are all deaccessioned, returns a little metadata:
		- Example code to include, maybe in a jupyter notebook:
			import json
			from pyDataverse.api import Api

			published_pid='doi:10.70122/FK2/EJEZTC'
			pid_not_exists='doi:10.7910/DVN/11111'
			pid_not_all_versions_deaccessioned='doi:10.70122/FK2/SIMAOW'
			pid_all_versions_deaccessioned='doi:10.70122/FK2/FZIM6W'

			api=Api(server)
			resp=api.get_dataset(pid_all_versions_deaccessioned)
			# resp=api.get_dataset(pid_not_all_versions_deaccessioned)
			print((json.dumps(resp.json(), indent=4)))

	- Let user enter API key to retreive the metadata of any unpublished datasets accessible by the Dataverse account.

	- When user hasn't chosen a text file and directory for the metadata files, pressing Start button 
	should tell user that she needs to choose a file and directory.

'''

import csv
import json
import os
import pandas as pd
from pyDataverse.api import Api
import time
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from urllib.request import urlopen
from urllib.parse import urlparse

# Create GUI for getting user input
window=Tk()
window.title('Get dataset metadata')
window.geometry('650x400') # width x height

# Create label for Dataverse repository URL
label_repositoryURL=Label(window, text='Enter Dataverse repository URL:', anchor='w')
label_repositoryURL.grid(sticky='w', column=0, row=0)

# Create Dataverse repository URL text box
repositoryURL=str()
entry_repositoryURL=Entry(window, width=50, textvariable=repositoryURL)
entry_repositoryURL.grid(sticky='w', column=0, row=1, pady=2)

# Create help text for server name field
label_dataverseUrlHelpText=Label(window, text='Example: https://demo.dataverse.org/', foreground='grey', anchor='w')
label_dataverseUrlHelpText.grid(sticky='w', column=0, row=2)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(3, minsize=25)

# Create label for Browse directory button
label_browseForFile=Label(window, text='Choose txt file contain list of dataset PIDs:', anchor='w')
label_browseForFile.grid(sticky='w', column=0, row=4, pady=2)

# Create Browse directory button
button_browseForFile=ttk.Button(window, text='Browse', command=lambda: retrieve_file())
button_browseForFile.grid(sticky='w', column=0, row=5)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(7, minsize=25)

# Create label for Browse directory button
label_browseDirectory=Label(window, text='Choose folder to put the metadata files folder into:', anchor='w')
label_browseDirectory.grid(sticky='w', column=0, row=8, pady=2)

# Create Browse directory button
button_browseDirectory=ttk.Button(window, text='Browse', command=lambda: retrieve_directory())
button_browseDirectory.grid(sticky='w', column=0, row=9)

# Create start button
button_Submit=ttk.Button(window, text='Start', command=lambda: retrieve_input())
button_Submit.grid(sticky='w', column=0, row=11, pady=40)

# Function called when Browse button is pressed for choosing text file with dataset PIDs
def retrieve_file():
	global dataset_pids

	# Call the OS's file directory window and store selected object path as a global variable
	dataset_pids=filedialog.askopenfilename(filetypes=[('Text files', '*.txt')])

	# Show user which file she chose
	label_showChosenFile=Label(window, text='You chose: ' + dataset_pids, anchor='w', foreground='green')
	label_showChosenFile.grid(sticky='w', column=0, row=6)

# Function called when Browse button is pressed
def retrieve_directory():
	global metadataFileDirectory

	# Call the OS's file directory window and store selected object path as a global variable
	metadataFileDirectory=filedialog.askdirectory()

	# Show user which directory she chose
	label_showChosenDirectory=Label(window, text='You chose: ' + metadataFileDirectory, anchor='w', foreground='green')
	label_showChosenDirectory.grid(sticky='w', column=0, row=10)

# Function called when Start button is pressed
def retrieve_input():
	# global dataset_pids
	# global metadataFileDirectory

	global repositoryURL

	# Store what's entered in dataverseUrl text box as a global variable
	repositoryURL=entry_repositoryURL.get()

	# # Store the file path of the text file chosen
	# # dataset_pids=button_browseForFile.get()

	# # Store the directory path chosen to store the metadata file directory
	# # metadataFileDirectory=button_browseForFile.get()

	# if not dataset_pids:
	# 	print('You must choose a text file containing a list of PIDs')
	# 	label_dataverseUrlReqiured=Label(window, text='You must choose a text file containing a list of PIDs.', foreground='red', anchor='w')
	# 	label_dataverseUrlReqiured.grid(sticky='w', column=0, row=3)

	# if not metadataFileDirectory:
	# 	print('You must choose a folder to put the metadata files folder into')
	# 	label_dataverseUrlReqiured=Label(window, text='You must choose a folder to put the metadata files folder into.', foreground='red', anchor='w')
	# 	label_dataverseUrlReqiured.grid(sticky='w', column=0, row=8)

	# If user chose text file and chose directory for storing metadata directory, close window and continue script
	# if dataset_pids and metadataFileDirectory:
	# 	window.destroy()
	window.destroy()

# Keep window open until it's closed
mainloop()

# Save current time to append it to main folder name
current_time=time.strftime('%Y.%m.%d_%H.%M.%S')

# Save directory with dataverse alias and current time
metadataFileDirectoryPath=os.path.join(metadataFileDirectory, 'dataset_metadata_%s' %(current_time))

# Create main directory
os.mkdir(metadataFileDirectoryPath)

# Download JSON metadata from APIs
print('Downloading JSON metadata to dataset_metadata folder:')

# Initiate count for terminal progress indicator
count=0

# Save number of items in the dataset_pids txt file in "total" variable
total=len(open(dataset_pids).readlines())

dataset_pids=open(dataset_pids)

# Use pyDataverse to establish connection with server
api=Api(repositoryURL)

# For each dataset persistent identifier in the txt file, download the dataset's Dataverse JSON file into the metadata folder
for pid in dataset_pids:

	# Remove any trailing spaces from pid
	pid=pid.rstrip()

	# Use the pid as the file name, replacing the colon and slashes with underscores
	filename='%s.json' %(pid.replace(':', '_').replace('/', '_'))

	# Use pyDataverse to get the metadata of the dataset
	resp=api.get_dataset(pid)

	# Write the JSON to the new file
	with open(os.path.join(metadataFileDirectoryPath, filename), mode='w') as f:
		f.write(json.dumps(resp.json(), indent=4))

	# Increase count variable to track progress
	count += 1

	# Print progress
	print('Downloaded %s of %s JSON files' %(count, total), end='\r', flush=True)

print('Downloaded %s of %s JSON files' %(count, total))
