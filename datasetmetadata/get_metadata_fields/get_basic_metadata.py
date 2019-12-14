# For each dataset listed in dataset_pids.txt, get basic metadata in Citation block, e.g. title, dates, versions

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
filename = os.path.join(current_directory,'basic_metadata.csv')

with open(filename, mode = 'w') as metadatafile:
	metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting=csv.QUOTE_MINIMAL)
	metadatafile.writerow(['dataset_id', 'persistentUrl','publicationdate','versionstate','latestversionnumber', 'versionreleasetime']) # Create header row

for file in glob.glob(os.path.join(folder_with_json_files, '*.json')): # For each JSON file in a folder
	with open(file, 'r') as f1: # Open each file in read mode
		dataset_metadata = f1.read() # Copy content to dataset_metadata variable
		dataset_metadata = json.loads(dataset_metadata) # Load content in variable as a json object

    # Save the metadata values in variables
	dataset_id = dataset_metadata['id']
	persistentUrl = dataset_metadata['persistentUrl']
	publicationDate = dataset_metadata['publicationDate']
	versionState = dataset_metadata['datasetVersion']['versionState']
	latestversionnumber = str(dataset_metadata['datasetVersion']['versionNumber']) + '.' + str(dataset_metadata['datasetVersion']['versionMinorNumber'])
	versionreleasetime = dataset_metadata['datasetVersion']['releaseTime']

	# Append fields to the csv file
	with open(filename, mode = 'a') as metadatafile:
		def to_utf8(lst):
			return [unicode(elem).encode('utf-8') for elem in lst] # Convert all characters to utf-8
		metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
		metadatafile.writerow([dataset_id, persistentUrl, publicationDate, versionState, latestversionnumber, versionreleasetime]) # Create header row