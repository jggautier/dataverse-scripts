'''
This script takes the metadatablock files retrieved by the get_dataset_metadata_of_all_installations.py script
and adds the metadatablock names and fields of each installation into a CSV file for further analysis.
'''

import csv
import json
import os
from pathlib import Path


# Function for getting list of non-hidden directories inside of a given directory
def listdir_nohidden(path):
    directories = []
    for f in os.listdir(path):
        if not f.startswith('.'):
            directories.append(f)
    return directories


# Enter path to directory that contains the folders and files created by the get_dataset_metadata_of_all_installations.py script
mainDirectory = ''

# Enter path to directory to store CSV file that this script will create
csvFileFolder = ''

csvFile = os.path.join(csvFileFolder, 'metadatablocks_from_most_known_dataverse_installations.csv')

with open(csvFile, mode='w', encoding='utf-8-sig') as data:
    data = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Create header row
    data.writerow([
        'installation_name_(Dataverse_version)', 'metadatablock_name', 
        'parentfield_name', 'subfield_name', 'display_name', 'description', 'watermark'])

count = 0
total = len(listdir_nohidden(mainDirectory))

# for repositoryFileName in os.listdir(mainDirectory):
for repositoryFileName in listdir_nohidden(mainDirectory):

    count += 1

    # Get the repository name
    size = len(repositoryFileName)
    repositoryName = repositoryFileName[:size - 20]
    # print(repositoryName)

    print(f'Parsing metadatablocks: {count} of {total}')

    # Open each installation folder
    repositoryFolderPath = os.path.join(mainDirectory, repositoryFileName)
    if os.path.isdir(repositoryFolderPath):

        for subFolder in os.listdir(repositoryFolderPath):
            if 'metadatablocks' in subFolder:
                metadatablockFolderPath = os.path.join(repositoryFolderPath, subFolder)

        # Open each .json file
        for metadatablockFile in os.listdir(metadatablockFolderPath):

            # Get only the metadatablock name from the name of each metadatablock JSON file
            metadatablockName = metadatablockFile.split('_v', 1)[0]
            version = metadatablockFile.split('_v', 1)[1].rstrip('.json')

            # Get repository name and combine with version
            repositoryNameVersion = f'{repositoryName}_({version})'

            metadatablockFilePath = os.path.join(metadatablockFolderPath, metadatablockFile)

            with open(metadatablockFilePath, mode='r', encoding='utf-8-sig') as f:  # Open file in read mode
                metadatablockData = f.read()  # Copy content to dataset_metadata variable
                metadatablockData = json.loads(metadatablockData)  # Load content as a python dict

                # Get the names of fields that have childfields
                compoundfields = []
                for parentfield in metadatablockData['data']['fields']:
                    properties = metadatablockData['data']['fields'][parentfield]
                    for property in properties:
                        if 'childFields' in properties:
                            field = properties[property]
                            compoundfields.append(field)
                            break

                allParentAndChildFields = []
                for parentfield in compoundfields:
                    # print(parentfield)
                    if parentfield in metadatablockData['data']['fields']:
                        properties = metadatablockData['data']['fields'][parentfield]
                        allParentAndChildFields.append(parentfield)
                        for subfield in properties['childFields']:
                            allParentAndChildFields.append(subfield)
                            subFieldDisplayName = properties['childFields'][subfield]['displayName']
                            subFieldDescription = properties['childFields'][subfield]['description']
                            subFieldWatermark = properties['childFields'][subfield]['watermark']

                            # Add parent and child names to the CSV file
                            with open(csvFile, mode='a', encoding='utf-8-sig') as data:
                                data = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                                # Write new row
                                data.writerow([
                                    repositoryNameVersion, metadatablockName, parentfield, subfield, 
                                    subFieldDisplayName, subFieldDescription, subFieldWatermark])

                # Get the names of all fields
                allFields = []
                for parentfield in metadatablockData['data']['fields']:
                    properties = metadatablockData['data']['fields'][parentfield]
                    for property in properties:
                        field = properties[property]
                        allFields.append(field)
                        break

                # Get names of primitives fields by removing list of compound and child fields from the list of all fields
                primitiveFields = list(set(allFields) - set(allParentAndChildFields))

                # Add the primitive field names to the CSV file
                for primitiveField in primitiveFields:
                    if primitiveField in metadatablockData['data']['fields']:
                        primitiveFieldDisplayName = metadatablockData['data']['fields'][primitiveField]['displayName']
                        primitiveFieldDescription = metadatablockData['data']['fields'][primitiveField]['description']
                        primitiveFieldWatermark = metadatablockData['data']['fields'][primitiveField]['watermark']

                    # Set subfield to an empty string so that Dataverse "ingests" the CSV file.
                    subfield = ''
                    with open(csvFile, mode='a', encoding='utf-8-sig') as data:
                        data = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                        # Write new row
                        data.writerow([
                            repositoryNameVersion, metadatablockName, primitiveField, subfield, 
                            primitiveFieldDisplayName, primitiveFieldDescription, primitiveFieldWatermark])
