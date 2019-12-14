# For each dataset listed in dataset_pids.txt, get the values of the author fields

import os
import json
import glob
import csv
from tkinter import filedialog
from tkinter import *

# Ask user to choose folder that contains JSON metadata files
root = Tk()
root.withdraw()
folder_with_json_files = filedialog.askdirectory()

# Create table in directory where script lives
current_directory = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(current_directory,'authors.csv')

with open(filename, mode = 'w') as metadatafile:
	metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
	metadatafile.writerow(['dataset_id', 'persistentUrl', 'authorName', 'authorAffiliation', 'authorIdentifierScheme', 'authorIdentifier']) # Create header row

for file in glob.glob(os.path.join(folder_with_json_files, '*.json')): # For each file in a folder of json files
	with open(file, 'r') as f1: # Open each file in read mode
		dataset_metadata = f1.read() # Copy content to dataset_metadata variable
		dataset_metadata = json.loads(dataset_metadata) # Overwrite variable with content as a json object

    # Count number of author compound fields
	for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
		if fields['typeName'] == 'author': # Find compound name
			total = len(fields['value'])

			# If there are author compound fields
			if total:
				index = 0
				condition = True

				while (condition):
					dataset_id = str(dataset_metadata['id']) # Save the dataset id of each dataset 
					persistentUrl = dataset_metadata['persistentUrl'] # Save the identifier of each dataset

					# Get authorName if there is one, or set authorName to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'author':  # Find compound name
								authorName = fields['value'][index]['authorName']['value'] # Find value in subfield
					except KeyError:
					    authorName = ''

					# Get authorAffiliation if there is one, or set authorAffiliation to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'author':  # Find compound name
								authorAffiliation = fields['value'][index]['authorAffiliation']['value'] # Find value in subfield
					except KeyError:
						authorAffiliation = ''

					# Get authorIdentifierScheme if there is one, or set authorIdentifierScheme to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'author':  # Find compound name
								authorIdentifierScheme = fields['value'][index]['authorIdentifierScheme']['value'] # Find value in subfield
					except KeyError:
						authorIdentifierScheme = ''

					# Get authorIdentifier if there is one, or set authorIdentifier to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'author':  # Find compound name
								authorIdentifier = fields['value'][index]['authorIdentifier']['value'] # Find value in subfield
					except KeyError:
						authorIdentifier = ''

					index += 1
					condition = index < total

					# Append fields to the csv file
					with open(filename, mode = 'a') as metadatafile:
						def to_utf8(lst):
							return [unicode(elem).encode('utf-8') for elem in lst] # Convert all characters to utf-8
						metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
						metadatafile.writerow([dataset_id, persistentUrl, authorName, authorAffiliation, authorIdentifierScheme, authorIdentifier])