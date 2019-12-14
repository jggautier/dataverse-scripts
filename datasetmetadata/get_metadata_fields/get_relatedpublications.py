# For each dataset listed in dataset_pids.txt, get the values of the related publication fields

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
filename = os.path.join(current_directory,'relatedpublication.csv')

with open(filename, mode = 'w') as metadatafile:
	metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
	metadatafile.writerow(['dataset_id', 'persistentUrl', 'publicationIDType', 'publicationIDNumber', 'publicationURL', 'publicationCitation']) # Create header row

for file in glob.glob(os.path.join(folder_with_json_files, '*.json')): # For each file in a folder of json files
	with open(file, 'r') as f1: # Open each file in read mode
		dataset_metadata = f1.read() # Copy content to dataset_metadata variable
		dataset_metadata = json.loads(dataset_metadata) # Overwrite variable with content as a json object

    # Count number of related publication compound fields
	for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
		if fields['typeName'] == 'publication': # Find compound name
			total = len(fields['value'])

			# If there are related publication compound fields
			if total:
				index = 0
				condition = True

				while (condition):
					dataset_id = str(dataset_metadata['id']) # Save the dataset id of each dataset 
					persistentUrl = dataset_metadata['persistentUrl'] # Save the identifier of each dataset

					# Get publicationIDType if there is one, or set publicationIDType to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'publication':  # Find compound name
								publicationIDType = fields['value'][index]['publicationIDType']['value'] # Find value in subfield
					except KeyError:
					    publicationIDType = ''

					# Get publicationIDNumber if there is one, or set publicationIDNumber to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'publication':  # Find compound name
								publicationIDNumber = fields['value'][index]['publicationIDNumber']['value'] # Find value in subfield
					except KeyError:
						publicationIDNumber = ''

					# Get publicationURL if there is one, or set publicationURL to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'publication':  # Find compound name
								publicationURL = fields['value'][index]['publicationURL']['value'] # Find value in subfield
					except KeyError:
						publicationURL = ''

					# Get publicationCitation if there is one, or set publicationCitation to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'publication':  # Find compound name
								publicationCitation = fields['value'][index]['publicationCitation']['value'] # Find value in subfield
					except KeyError:
						publicationCitation = ''

					index += 1
					condition = index < total

					# Append fields to the csv file
					with open(filename, mode = 'a') as metadatafile:
						def to_utf8(lst):
							return [unicode(elem).encode('utf-8') for elem in lst] # Convert all characters to utf-8
						metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
						metadatafile.writerow([dataset_id, persistentUrl, publicationIDType, publicationIDNumber, publicationURL, publicationCitation])

