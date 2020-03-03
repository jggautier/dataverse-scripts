# Python script for getting the dataverse names of given dataset PIDs

import csv
import json
import os
from pyDataverse.api import Api
import time
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from urllib.request import urlopen
from urllib.parse import urlparse

# Create GUI for getting user input
window=Tk()
window.title('Get dataverse names')
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
label_browseDirectory=Label(window, text='Choose folder to put csv file into:', anchor='w')
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
	global csvDirectory

	# Call the OS's file directory window and store selected object path as a global variable
	csvDirectory=filedialog.askdirectory()

	# Show user which directory she chose
	label_showChosenDirectory=Label(window, text='You chose: ' + csvDirectory, anchor='w', foreground='green')
	label_showChosenDirectory.grid(sticky='w', column=0, row=10)

# Function called when Start button is pressed
def retrieve_input():
	global repositoryURL

	# Store what's entered in dataverseUrl text box as a global variable
	repositoryURL=entry_repositoryURL.get()

	window.destroy()

# Keep window open until it's closed
mainloop()

filename=os.path.join(csvDirectory,'dataversenames.csv')

# Create CSV file
with open(filename, mode='w') as opencsvfile:
	opencsvfile=csv.writer(opencsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	
	# Create header row
	opencsvfile.writerow(['datasetUrl', 'dataset_id', 'dataverseName'])

dataset_pids=open(dataset_pids)

piderrors=[]

for pid in dataset_pids:
	# Construct "Get Versions" API endpoint url
	try:
		if apikey:
			url='%s/api/search?q="%s"&type=dataset&key=%s' %(server, pid, apikey)
		else:
			url='%s/api/search?q="%s"&type=dataset' %(server, pid)
		# Store dataset and file info from API call to "data" variable
		data=json.load(urlopen(url))
	except urllib.error.URLError:
		piderrors.append(pid)

	# Save dataset PID and dataverse name
	dataset_id= # Dataset_id isn't in Search API :( Need another endpoint to get dataset_id
	persistentUrl=data['data']['items'][0]['url']
	dataverseName=data['data']['items'][0]['name_of_dataverse']
	
	# print('%s is in %s' %(datasetPersistentId, dataverseName))

	# Write values of the three variables to a new row in the CSV
	with open(filename, mode='a') as datasets:

		# Convert all characters to utf-8
		def to_utf8(lst):
			return [unicode(elem).encode('utf-8') for elem in lst]

		datasets=csv.writer(datasets, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		datasets.writerow([dataset_id, persistentUrl, dataverseName])

print('Copied PIDs:', total, 'of total:', total)