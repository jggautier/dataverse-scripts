# For each dataset listed in dataset_pids.txt, get the values of the keyword fields

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
filename = os.path.join(current_directory,'keywords.csv')

with open(filename, mode = 'w') as metadatafile:
	metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
	metadatafile.writerow(['dataset_id', 'persistentUrl', 'keywordValue', 'keywordVocabulary', 'keywordVocabularyURI']) # Create header row

for file in glob.glob(os.path.join(folder_with_json_files, '*.json')): # For each file in a folder of json files
	with open(file, 'r') as f1: # Open each file in read mode
		dataset_metadata = f1.read() # Copy content to dataset_metadata variable
		dataset_metadata = json.loads(dataset_metadata) # Overwrite variable with content as a json object

    # Count number of keyword compound fields
	for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
		if fields['typeName'] == 'keyword': # Find compound name
			total = len(fields['value'])

			# If there are keyword compound fields
			if total:
				index = 0
				condition = True

				while (condition):
					id = str(dataset_metadata['id']) # Save the dataset id of each dataset 
					persistentUrl = dataset_metadata['persistentUrl'] # Save the persistentUrl of each dataset

					# Get keywordValue if there is one or set keywordValue to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'keyword':  # Find compound name
								keywordValue = fields['value'][index]['keywordValue']['value'] # Find value in subfield
					except KeyError:
					    keywordValue = ''

					# Get keywordVocabulary if there is one or set keywordVocabulary to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'keyword':  # Find compound name
								keywordVocabulary = fields['value'][index]['keywordVocabulary']['value'] # Find value in subfield
					except KeyError:
						keywordVocabulary = ''

					# Get keywordVocabularyURI if there is one or set keywordVocabularyURI to blank
					try:
						for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
							if fields['typeName'] == 'keyword':  # Find compound name
								keywordVocabularyURI = fields['value'][index]['keywordVocabularyURI']['value'] # Find value in subfield
					except KeyError:
						keywordVocabularyURI = ''

					index += 1
					condition = index < total

					# Append fields to the csv file
					with open(filename, mode = 'a') as metadatafile:
						def to_utf8(lst):
							return [unicode(elem).encode('utf-8') for elem in lst] # Convert all characters to utf-8
						metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
						metadatafile.writerow([id, persistentUrl, keywordValue, keywordVocabulary, keywordVocabularyURI])