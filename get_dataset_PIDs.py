# For a given dataverse, get its sub-dataverses or datasets. Includes deaccessioned datasets. Excludes harvested and linked datasets.

import csv
import glob
import json
import os
import sys
import time
from tkinter import filedialog
from tkinter import ttk
from tkinter import *
import urllib.request
from urllib.request import urlopen
from urllib.parse import urlparse

####################################################################################
# Create GUI for getting user input
window=Tk()
window.title('Get dataset PIDs')
window.geometry('475x450') # width x height

# Function called when Browse button is pressed
def retrieve_directory():
	global directory

	# Call the OS's file directory window and store selected object path as a global variable
	directory=filedialog.askdirectory()

	# Show user which directory she chose
	label_showChosenDirectory=Label(window, text='You chose: ' + directory, anchor='w', foreground='green')
	label_showChosenDirectory.grid(sticky='w', column=0, row=13)

# Function called when Start button is pressed
def retrieve_input():
	global dataverseUrl
	global apikey
	global get_subdataverses

	# Record if user wants to search in subdataverses
	get_subdataverses=get_subdataverses.get()

	# Store what entered in the api key text box as a global variable
	apikey=entry_apikey.get()

	# Store what's entered in dataverseUrl text box as a global variable
	dataverseUrl=entry_dataverseUrl.get()

	# If user enters text in dataverseUrl text box, strip any white characters
	if dataverseUrl:
		dataverseUrl=str(dataverseUrl)
		dataverseUrl=dataverseUrl.strip()

		# If user also selected a directory, close the window
		if directory:
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

# Create help text for Dataverse URL field
label_dataverseUrlHelpText=Label(window, text='Example: https://demo.dataverse.org/dataverse/dataversealias', foreground='grey', anchor='w')
label_dataverseUrlHelpText.grid(sticky='w', column=0, row=2)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(4, minsize=25)

get_subdataverses=IntVar()
c=Checkbutton(window, text="Include subdataverses", variable=get_subdataverses).grid(sticky='w', column=0, row=5)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(6, minsize=25)

# Create label for API key field
label_apikey=Label(window, text='API key:', anchor='w')
label_apikey.grid(sticky='w', column=0, row=7)

# Create API key field
apikey=str()
entry_apikey=Entry(window, width=50, textvariable=apikey)
entry_apikey.grid(sticky='w', column=0, row=8, pady=2)

# Create help text for API key field
label_apikeyHelpText=Label(window, text='If no API is entered, only published datasets will be found', foreground='grey', anchor='w')
label_apikeyHelpText.grid(sticky='w', column=0, row=9)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(10, minsize=25)

# Create label for Browse directory button
label_browseDirectory=Label(window, text='Choose folder to store list of dataset PIDs:', anchor='w')
label_browseDirectory.grid(sticky='w', column=0, row=11, pady=2)

# Create Browse directory button
button_browseDirectory=ttk.Button(window, text='Browse', command=lambda: retrieve_directory())
button_browseDirectory.grid(sticky='w', column=0, row=12)

# Create start button
button_Submit=ttk.Button(window, text='Start', command=lambda: retrieve_input())
button_Submit.grid(sticky='w', column=0, row=14, pady=40)

# Keep window open until it's closed
mainloop()

# Parse dataverseUrl to get server name and alias
parsed=urlparse(dataverseUrl)
server=parsed.scheme + '://' + parsed.netloc
alias=parsed.path.split('/')[2]

# Save current time to append it to main folder name
current_time=time.strftime('%Y.%m.%d_%H.%M.%S')

####################################################################################

# Get ID of given dataverse alias
if apikey:
	url='%s/api/dataverses/%s?key=%s' %(server, alias, apikey)
else:
	url='%s/api/dataverses/%s' %(server, alias)

data=json.load(urlopen(url))
parent_dataverse_id=data['data']['id']

# Create list and add ID of given dataverse
dataverse_ids=[parent_dataverse_id]


# If user wants datasets in subdataverses, search for and include IDs of subdataverses (exludes linked dataverses)

# Get each sub-dataverse in the given dataverse
if get_subdataverses==1:
	print('Getting dataverse IDs in %s:' %(alias))

	for dataverse_id in dataverse_ids:
		# As a progress indicator, print a dot each time a row is written
		sys.stdout.write('.')
		sys.stdout.flush()
		if apikey:
			url='%s/api/dataverses/%s/contents?key=%s' %(server, dataverse_id, apikey)
		else:
			url='%s/api/dataverses/%s/contents' %(server, dataverse_id)
		data=json.load(urlopen(url))
		for i in data['data']:
			if i['type']=='dataverse':
				dataverse_id=i['id']
				dataverse_ids.extend([dataverse_id])

	print('\nFound 1 dataverse and %s subdataverses' %(len(dataverse_ids)-1))

####################################################################################
# For each dataverse in the list, add the PIDs of all datasets to a text file - excludes linked and harvested datasets

txtfile='dataset_pids-%s(%s).txt' %(alias, current_time)
txtfilepath=os.path.join(directory, txtfile)

print('Writing dataset IDs to %s:' %(txtfilepath))

count=0

with open(txtfilepath, mode='w') as opentxtfile:
	for id in dataverse_ids:
		if apikey:
			url='%s/api/dataverses/%s/contents?key=%s' %(server, id, apikey)
		else:
			url='%s/api/dataverses/%s/contents' %(server, id)
		data=json.load(urlopen(url))

		for i in data['data']:
			if i['type']=='dataset':
				protocol=i['protocol']
				authority=i['authority']
				identifier=i['identifier']
				dataset_pid='%s:%s/%s' %(protocol, authority, identifier)
				
				count+=1

				# Create new row with dataset and file info
				opentxtfile.write('%s\n' %(dataset_pid))

				# As a progress indicator, print a dot each time a row is written
				sys.stdout.write('.')
				sys.stdout.flush()


print('\nDatasets written to .txt file: %s' %(count))