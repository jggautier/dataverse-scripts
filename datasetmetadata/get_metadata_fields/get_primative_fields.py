# For each dataset listed in dataset_pids.csv, get the values of any fields that are primitive (don't have subfields)

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

# Create directories

# create parent directory
current_directory = os.path.dirname(os.path.realpath(__file__)) # save directory of this python file
parent_directory_path = os.path.join(current_directory, 'tables_2')
os.mkdir(parent_directory_path)


# Fields that allow only one value
primativefields_nomultiples = ['title', 'subtitle', 'alternativeTitle', 'alternativeURL', 'notesText', 'productionDate', 'productionPlace', 'distributionDate', 'depositor', 'dateOfDeposit', 'originOfSources', 'characteristicOfSources', 'accessToSources']

for fieldname in primativefields_nomultiples:

	filename = os.path.join(parent_directory_path,'%s.csv' %(fieldname))

	with open(filename, mode = 'w') as metadatafile:
		metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
		metadatafile.writerow(['dataset_id', 'persistentUrl', fieldname]) # Create header row
	
	print('Getting %s metadata...' %(fieldname))

	# For each file in a folder of json files
	for file in glob.glob(os.path.join(folder_with_json_files, '*.json')): 	

		# Open each file in read mode
		with open(file, 'r') as f1:
			
			# Copy content to dataset_metadata variable
			dataset_metadata = f1.read()

			# Overwrite variable with content as a json object
			dataset_metadata = json.loads(dataset_metadata)

		# Save the dataset id of each dataset 
		# dataset_id = str(dataset_metadata['id'])

	    # Couple each field value with the dataset_id and write as a row to subjects.csv
		for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
			if fields['typeName'] == fieldname:
				value = fields['value']
				persistentUrl = dataset_metadata['persistentUrl']
				dataset_id = str(dataset_metadata['id'])
				# with open('/Users/juliangautier/Desktop/tables/%s.csv' %(fieldname), mode = 'a') as metadatafile:
				with open(filename, mode = 'a') as metadatafile:

					# Convert all characters to utf-8 to avoid encoding errors when writing to the csv file
					def to_utf8(lst):
						return [unicode(elem).encode('utf-8') for elem in lst]

					metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
					metadatafile.writerow([dataset_id, persistentUrl, value])


# Fields that allow multiple values
primativefields_multiples = ['subject', 'language', 'kindOfData', 'relatedMaterial', 'relatedDatasets', 'otherReferences', 'dataSources', ]

for fieldname in primativefields_multiples:

	filename = os.path.join(parent_directory_path,'%s.csv' %(fieldname))

	with open(filename, mode = 'w') as metadatafile:
		metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
		metadatafile.writerow(['dataset_id', 'persistentUrl', fieldname]) # Create header row

	print('Getting %s metadata...' %(fieldname))
	
	# For each file in a folder of json files
	for file in glob.glob(os.path.join(folder_with_json_files, '*.json')): 
		
		# Open each file in read mode
		with open(file, 'r') as f1:
			
			# Copy content to dataset_metadata variable
			dataset_metadata = f1.read()

			# Overwrite variable with content as a json object
			dataset_metadata = json.loads(dataset_metadata)

		# Save the dataset id of each dataset 
		dataset_id = str(dataset_metadata['id'])

	    # Couple each field value with the dataset_id and write as a row to subjects.csv
		for fields in dataset_metadata['datasetVersion']['metadataBlocks']['citation']['fields']:
			if fields['typeName'] == fieldname:
				for value in fields['value']:
					persistentUrl = dataset_metadata['persistentUrl']
					with open(filename, mode = 'a') as metadatafile:

						# Convert all characters to utf-8 to avoid encoding errors when writing to the csv file
						def to_utf8(lst):
							return [unicode(elem).encode('utf-8') for elem in lst]

						metadatafile = csv.writer(metadatafile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
						metadatafile.writerow([dataset_id, persistentUrl, value])