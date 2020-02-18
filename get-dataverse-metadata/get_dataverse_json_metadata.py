# Python script for downloading the Dataverse JSON metadata files of given list of datasets PIDs

'''
To-do
	- Replace pyDataverse with urllib
		- In the get_dataset_pids.py, I'm replacing the Search API with the Native API's "get contents" endpoint, 
		which can include datasets that have been deaccessioned. I think pyDataverse needs to change how it retrieves metadata of
		datasets whose version have all been deaccessioned.
			- When using pyDataverse to retrieve the metadata of datasets whose versions have all been deaccessioned,
			pyDataverse returns a limited amount of metadata instead of returning an error. (I think it should return all metadata,
			since Dataverse tells users that metadata is always available, but that needs to be fixed in the Dataverse app.)
	- Report issue with pyDataverse
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

	- With urllib, use try/except where the exception is a 403 error (probably because the PID doesn't exist or all versions are deaccessioned).
	When the exception is met, print in the terminal or print to a text file a list of given PIDs whose dataverse-json can't be retrieved.
		Code:
			try:
				response=urllib.request.urlopen('%s/api/datasets/export?exporter=json_exportformat&persistentId=%s' %(server, pid))
				source=response.read()
				data=json.loads(source)
				data=json.dumps(data, indent=4)
				print(data)

			# If there's an error (probably because all versions of the dataset are deaccessioned), continue to next dataset
			except urllib.error.URLError:
				print('Dataset with Persistent ID %s not found or deaccessioned.' %(pid))

'''

import csv
import json
import os
import pandas as pd
from pyDataverse.api import Api
import time
from tkinter import filedialog
from tkinter import ttk
from tkinter import *
from urllib.request import urlopen
from urllib.parse import urlparse

# Create GUI for getting user input
window=Tk()
window.title('Get dataset metadata')
window.geometry('475x275') # width x height

# Function called when Browse button is pressed
def retrieve_directory():
	global mainDirectory

	# Call the OS's file directory window and store selected object path as a global variable
	mainDirectory=filedialog.askdirectory()

	# Show user which directory she chose
	label_showChosenDirectory=Label(window, text='You chose: ' + mainDirectory, anchor='w', foreground='green')
	label_showChosenDirectory.grid(sticky='w', column=0, row=7)

# Function called when Start button is pressed
def retrieve_input():
	global dataverseUrl

	# Store what's entered in dataverseUrl text box as a global variable
	dataverseUrl=entry_dataverseUrl.get()

	# If user enters text in dataverseUrl text box, strip any white characters
	if dataverseUrl:
		dataverseUrl=str(dataverseUrl)
		dataverseUrl=dataverseUrl.strip()

		# If user also selected a directory, close the window
		if mainDirectory:
			window.destroy()

	# If no dataverseUrl is entered, display message that one is required
	else:
		print('A dataverse URL is required')
		label_dataverseUrlReqiured=Label(window, text='A dataverse URL is required.', foreground='red', anchor='w')
		label_dataverseUrlReqiured.grid(sticky='w', column=0, row=3)

# Create label for Dataverse URL field
label_dataverseUrl=Label(window, text='Dataverse URL:', anchor='w')
label_dataverseUrl.grid(sticky='w', column=0, row=0)

# Create Dataverse URL field
dataverseUrl=str()
entry_dataverseUrl=Entry(window, width=50, textvariable=dataverseUrl)
entry_dataverseUrl.grid(sticky='w', column=0, row=1, pady=2)

# Create help text before URL field
label_dataverseUrlHelpText=Label(window, text='Example: https://demo.dataverse.org/dataverse/dataversealias', foreground='grey', anchor='w')
label_dataverseUrlHelpText.grid(sticky='w', column=0, row=2)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(4, minsize=25)

# Create label for Browse directory button
label_browseDirectory=Label(window, text='Choose folder to store metadata files:', anchor='w')
label_browseDirectory.grid(sticky='w', column=0, row=5, pady=2)

# Create Browse directory button
button_browseDirectory=ttk.Button(window, text='Browse', command=lambda: retrieve_directory())
button_browseDirectory.grid(sticky='w', column=0, row=6)

# Create start button
button_Submit=ttk.Button(window, text='Start', command=lambda: retrieve_input())
button_Submit.grid(sticky='w', column=0, row=8, pady=40)

# Keep window open until it's closed
mainloop()

# Parse dataverseUrl to get server name and alias
parsed=urlparse(dataverseUrl)
server=parsed.scheme + '://' + parsed.netloc
alias=parsed.path.split('/')[2]

# Create directories

# Create main directory

# Save current time to append it to main folder name
current_time=time.strftime('%Y.%m.%d_%H.%M.%S')

# Save main directory with dataverse alias and current time
main_directory_path=os.path.join(mainDirectory, '%s_dataset_metadata_%s' %(alias, current_time))

# Create main directory
os.mkdir(main_directory_path)

# Create directory within main directory for the JSON metadata files
metadata_directory_path=os.path.join(main_directory_path, 'dataset_metadata')
os.mkdir(metadata_directory_path)
json_directory_path=os.path.join(main_directory_path, 'dataset_metadata/json')
os.mkdir(json_directory_path)


# Download JSON metadata from APIs
print('Downloading JSON metadata in dataset_metadata folder...')

# Save CSV file as a pandas dataframe
file=pd.read_csv(filename)

# Convert global_id column into a list
dataset_pids=file['global_id'].tolist()

# Initiate count for terminal progress indicator
start=1

# Save number of items in the dataset_pids list in "total" variable
total=len(dataset_pids)

# Use pyDataverse to establish connection with server
api = Api(server)

# For each dataset persistent identifier in the list, download the dataset's Dataverse JSON file into the metadata folder
for pid in dataset_pids:

	# Use pyDataverse to get the metadata of the dataset
	resp=api.get_dataset(pid)

	# Use the PID as the file name, replacing the colon and slashes with underscores
	filename='%s.json' %(pid.replace(':', '_').replace('/', '_'))

	# Write the JSON to the new file
	with open(os.path.join(json_directory_path, filename), mode='w') as f:
		f.write(json.dumps(resp.json(), indent=4))

	# Print progress
	print('Downloaded %s of %s JSON files' %(start, total), end='\r', flush=True)

	# Increase start variable to get next pid
	start += 1

print('Downloaded %s of %s JSON files' %(total, total))
