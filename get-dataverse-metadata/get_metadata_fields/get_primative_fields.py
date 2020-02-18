# For each dataset listed in dataset_pids.csv, get the values of any fields that are primitive (don't have subfields)

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
window.title('Get metadata from primitive fields')
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

# Fields that allow only one value
primativefields_nomultiples=['title', 'subtitle', 'alternativeTitle', 'alternativeURL', 'notesText', 'productionDate', 'productionPlace', 'distributionDate', 'depositor', 'dateOfDeposit', 'originOfSources', 'characteristicOfSources', 'accessToSources']

for fieldname in primativefields_nomultiples:

	# Store path of csv file to filename variable
	filename=os.path.join(csvDirectory,'%s.csv' %(fieldname))

	with open(filename, mode='w') as metadatafile:
		metadatafile=csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		metadatafile.writerow(['dataset_id', 'persistentUrl', fieldname]) # Create header row
	
	print('\nGetting %s metadata' %(fieldname))

	# For each file in a folder of json files
	for file in glob.glob(os.path.join(jsonDirectory, '*.json')): 	

		# Open each file in read mode
		with open(file, 'r') as f1:
			
			# Copy content to dataset_metadata variable
			dataset_metadata=f1.read()

			# Overwrite variable with content as a json object
			dataset_metadata=json.loads(dataset_metadata)

	    # Couple each field value with the dataset_id and write as a row to subjects.csv
		for fields in dataset_metadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
			if fields['typeName']==fieldname:
				value=fields['value']
				persistentUrl=dataset_metadata['data']['persistentUrl']
				dataset_id=str(dataset_metadata['data']['id'])

				with open(filename, mode='a') as metadatafile:

					# Convert all characters to utf-8 to avoid encoding errors when writing to the csv file
					def to_utf8(lst):
						return [unicode(elem).encode('utf-8') for elem in lst]

					metadatafile=csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
					
					# Write new row
					metadatafile.writerow([dataset_id, persistentUrl, value])

					# As a progress indicator, print a dot each time a row is written
					sys.stdout.write('.')
					sys.stdout.flush()

# Fields that allow multiple values
primativefields_multiples=['subject', 'language', 'kindOfData', 'relatedMaterial', 'relatedDatasets', 'otherReferences', 'dataSources', ]

for fieldname in primativefields_multiples:

	# Store path of csv file to filename variable
	filename=os.path.join(csvDirectory,'%s.csv' %(fieldname))

	with open(filename, mode='w') as metadatafile:
		metadatafile=csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		
		# Create header row
		metadatafile.writerow(['dataset_id', 'persistentUrl', fieldname])

	print('\nGetting %s metadata' %(fieldname))
	
	# For each file in a folder of json files
	for file in glob.glob(os.path.join(jsonDirectory, '*.json')): 
		
		# Open each file in read mode
		with open(file, 'r') as f1:
			
			# Copy content to dataset_metadata variable
			dataset_metadata=f1.read()

			# Overwrite variable with content as a json object
			dataset_metadata=json.loads(dataset_metadata)

		# Save the dataset id of each dataset 
		dataset_id=str(dataset_metadata['data']['id'])

	    # Couple each field value with the dataset_id and write as a row to subjects.csv
		for fields in dataset_metadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
			if fields['typeName']==fieldname:
				for value in fields['value']:
					persistentUrl=dataset_metadata['data']['persistentUrl']
					with open(filename, mode='a') as metadatafile:

						# Convert all characters to utf-8 to avoid encoding errors when writing to the csv file
						def to_utf8(lst):
							return [unicode(elem).encode('utf-8') for elem in lst]

						metadatafile=csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
						
						# Write new row
						metadatafile.writerow([dataset_id, persistentUrl, value])

						# As a progress indicator, print a dot each time a row is written
						sys.stdout.write('.')
						sys.stdout.flush()
print('\n')
