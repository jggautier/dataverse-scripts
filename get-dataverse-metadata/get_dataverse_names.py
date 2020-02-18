# Python script for getting the dataverse names of given dataset PIDs

import csv
import json
import os
import time
from tkinter import filedialog
from tkinter import ttk
from tkinter import *

# Create GUI for getting user input
window=Tk()
window.title('Get dataset PIDs')
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
label_browseDirectory=Label(window, text='Choose folder to store list of dataset PIDs:', anchor='w')
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

# Use Search API to get persistent identifiers, persistentUrls and dataverse names of datasets in the given dataverse

# Store path of CSV file to filename variable
filename=os.path.join(main_directory_path,'%s_dataset_pids.csv' %(alias))

print('Copying dataset PIDs to dataset_pids.csv...')

# Create CSV file and create header row
with open(filename, mode='w') as metadatafile:
	metadatafile=csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	metadatafile.writerow(['global_id', 'persistentUrl', 'dataverse']) 

# Initiate counts for pagination and terminal progress indicator
rows=10
start=0
condition=True

# Query string for search API, e.g. '*&type=dataverse'
query='*&type=dataset'

while (condition):
	# url=server + '/api/search?q=' + query + '&subtree=' + alias + '&start=' + str(start)
	url='%s/api/search?q=%s&subtree=%s&start=%s' %(server, query, alias, start)
	data=json.load(urlopen(url))

	# Save total count of datasets
	total=data['data']['total_count']
	
	# Print progress
	print('Copied PIDs: %s of total: %s' %(start, total), end='\r', flush=True)

	for i in data['data']['items']:
		
		# Get global_id
		global_id=i.get('global_id')

		# Get dataset's dataverse name
		dataverse=i.get('name_of_dataverse')		
		
		# Get persistentUrl
		persistentUrl=i.get('url')
		
		# Write values of the three variables to a new row in the CSV
		with open(filename, mode='a') as datasets:

			# Convert all characters to utf-8
			def to_utf8(lst):
				return [unicode(elem).encode('utf-8') for elem in lst]

			datasets=csv.writer(datasets, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			datasets.writerow([global_id, persistentUrl, dataverse])

	# Increase value of start
	start=start + rows
	
	# Set condition to true if start is less then total, so script gets the next page,
	# or false if start is more than total, which ends the while loop
	condition=start < total

print('Copied PIDs:', total, 'of total:', total)