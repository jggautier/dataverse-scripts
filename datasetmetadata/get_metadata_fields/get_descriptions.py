# For each dataset listed in dataset_pids.txt, get the values of the description fields

import os
import json
import glob
import csv
from tkinter import filedialog
from tkinter import *

# Ask user to choose folder that contains JSON metadata files
root = Tk()
root.withdraw()
# root.update()
folder_with_json_files = filedialog.askdirectory()

# Create table in directory where script lives
current_directory = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(current_directory,'descriptions.csv')

with open(filename, mode = 'w') as metadatafile:
	metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
	metadatafile.writerow(['dataset_id', 'persistentUrl', 'dsDescriptionValue', 'dsDescriptionDate']) # Create header row

for file in glob.glob(os.path.join(folder_with_json_files, '*.json')): # For each file in a folder of json files
	with open(file, 'r') as f1: # Open each file in read mode
		dataset_metadata = f1.read() # Copy content to dataset_metadata variable
		dataset_metadata = json.loads(dataset_metadata) # Overwrite variable with content as a json object

    # Count number of description compound fields
	for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
		if fields['typeName'] == 'dsDescription':
			total = len(fields['value'])

			# If there are description compound fields
			if total:
				index = 0
				condition = True

				while (condition):
					id = str(dataset_metadata['id']) # Save the dataset id of each dataset 
					persistentUrl = dataset_metadata['persistentUrl'] # Save the identifier of each dataset

					# Get dsDescriptionValue if there is one or set dsDescriptionValue to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'dsDescription': # Find compound name
								dsDescriptionValue = fields['value'][index]['dsDescriptionValue']['value'] # Find value in subfield
					except KeyError:
						dsDescriptionValue = ''

					# Get dsDescriptionDate if there is one or set dsDescriptionDate to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'dsDescription':
								dsDescriptionDate = fields['value'][index]['dsDescriptionDate']['value']
					except KeyError:
						dsDescriptionDate = ''
					condition = index < total

					# Append fields to the csv file
					with open(filename, mode = 'a') as metadatafile:
						def to_utf8(lst):
							return [unicode(elem).encode('utf-8') for elem in lst] # Convert all characters to utf-8
						metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
						metadatafile.writerow([id, persistentUrl, dsDescriptionValue, dsDescriptionDate])