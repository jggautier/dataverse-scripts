# For each dataset listed in dataset_pids.txt, get the values of the author fields

import csv
import json
import glob
import os
from tkinter import filedialog
from tkinter import ttk
from tkinter import *

# Create GUI for getting user input

# Create, title and size the window
window=Tk()
window.title('Get author metadata')
window.geometry('550x250') # width x height

# Function called when Browse button is pressed
def retrieve_jsondirectory():
	global jsonDirectory

	# Call the OS's file directory window and store selected object path as a global variable
	jsonDirectory=filedialog.askdirectory()

	# Show user which directory she chose
	label_showChosenDirectory=Label(window, text='You chose: ' + jsonDirectory, anchor='w', foreground='green')
	label_showChosenDirectory.grid(sticky='w', column=0, row=2)

# Function called when Browse button is pressed
def retrieve_csvdirectory():
	global csvDirectory

	# Call the OS's file directory window and store selected object path as a global variable
	csvDirectory=filedialog.askdirectory()

	# Show user which directory she chose
	label_showChosenDirectory=Label(window, text='You chose: ' + csvDirectory, anchor='w', foreground='green')
	label_showChosenDirectory.grid(sticky='w', column=0, row=6)

# Function called when Browse button is pressed
def start():
	window.destroy()

# Create label for button to browse for directory containing JSON files
label_getJSONFiles=Label(window, text='Choose folder containing the JSON files:', anchor='w')
label_getJSONFiles.grid(sticky='w', column=0, row=0, pady=2)

# Create button to browse for directory containing JSON files
button_getJSONFiles=ttk.Button(window, text='Browse', command=lambda: retrieve_jsondirectory())
button_getJSONFiles.grid(sticky='w', column=0, row=1)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(3, minsize=25)

# Create label for button to browse for directory to add csv files in
label_tablesDirectory=Label(window, text='Choose folder to store the csv files:', anchor='w')
label_tablesDirectory.grid(sticky='w', column=0, row=4, pady=2)

# Create button to browse for directory containing JSON files
button_tablesDirectory=ttk.Button(window, text='Browse', command=lambda: retrieve_csvdirectory())
button_tablesDirectory.grid(sticky='w', column=0, row=5)

# Create start button
button_Start=ttk.Button(window, text='Start', command=lambda: start())
button_Start.grid(sticky='w', column=0, row=7, pady=40)

# Keep window open until it's closed
mainloop()

# Create table in directory where script lives
filename=os.path.join(csvDirectory,'authors.csv')

print('Creating CSV file')

with open(filename, mode='w') as metadatafile:
	metadatafile=csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	metadatafile.writerow(['dataset_id', 'persistentUrl', 'authorName', 'authorAffiliation', 'authorIdentifierScheme', 'authorIdentifier']) # Create header row

print('Getting metadata:')

# For each file in a folder of json files
for file in glob.glob(os.path.join(jsonDirectory, '*.json')):
	
	# Open each file in read mode
	with open(file, 'r') as f1:
		
		# Copy content to dataset_metadata variable
		dataset_metadata=f1.read()

		# Overwrite variable with content as a json object
		dataset_metadata=json.loads(dataset_metadata)

    # Count number of author compound fields
	for fields in dataset_metadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
		if fields['typeName']=='author': # Find compound name
			total=len(fields['value'])

			# If there are author compound fields
			if total:
				index=0
				condition=True

				while (condition):

					# Save the dataset id of each dataset 
					dataset_id=str(dataset_metadata['data']['id'])

					# Save the identifier of each dataset
					persistentUrl=dataset_metadata['data']['persistentUrl']

					# Get authorName if there is one, or set authorName to blank
					try:
						for fields in dataset_metadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName']=='author':  # Find compound name
								authorName=fields['value'][index]['authorName']['value'] # Find value in subfield
					except KeyError:
						authorName=''

					# Get authorAffiliation if there is one, or set authorAffiliation to blank
					try:
						for fields in dataset_metadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
							
							# Find compound name
							if fields['typeName']=='author':
								
								# Find value in subfield
								authorAffiliation=fields['value'][index]['authorAffiliation']['value']
					except KeyError:
						authorAffiliation=''

					# Get authorIdentifierScheme if there is one, or set authorIdentifierScheme to blank
					try:
						for fields in dataset_metadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
							
							# Find compound name
							if fields['typeName']=='author':
								
 								# Find value in subfield
								authorIdentifierScheme=fields['value'][index]['authorIdentifierScheme']['value']
					except KeyError:
						authorIdentifierScheme=''

					# Get authorIdentifier if there is one, or set authorIdentifier to blank
					try:
						for fields in dataset_metadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
							
							# Find compound name
							if fields['typeName']=='author':
								
 								# Find value in subfield
								authorIdentifier=fields['value'][index]['authorIdentifier']['value']
					except KeyError:
						authorIdentifier=''

					index += 1
					condition=index < total

					# Append fields to the csv file
					with open(filename, mode='a') as metadatafile:

						# Convert all characters to utf-8
						def to_utf8(lst):
							return [unicode(elem).encode('utf-8') for elem in lst]

						metadatafile=csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
						
						# Write new row
						metadatafile.writerow([dataset_id, persistentUrl, authorName, authorAffiliation, authorIdentifierScheme, authorIdentifier])

						# As a progress indicator, print a dot each time a row is written
						sys.stdout.write('.')
						sys.stdout.flush()
print('\n')