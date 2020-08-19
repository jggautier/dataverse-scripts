'''
This script takes the metadatablock files retrieved by the get_dataset_metadata_of_all_installations.py script
and adds the metadatablock names and fields of each installation into a CSV file for further analysis.
'''

import csv
import json
import os
from pathlib import Path
import re

# Enter path to directory that contains the folders and files created by the get_dataset_metadata_of_all_installations.py script
main_directory = ''

# Enter path to directory to store CSV file that this script will create
csvfile_folder = ''

csvfile = str(Path(csvfile_folder + '/' + 'metadatablocks.csv'))

with open(csvfile, mode='w') as data:
    data = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Create header row
    data.writerow(['installation_name_(Dataverse_version)', 'metadatablock_name', 'parentfield_name', 'subfield_name'])

for repository_name in os.listdir(main_directory):

    # Get the repository name
    repository_name = repository_name

    # Open each installation folder
    repository_folder_path = str(Path(main_directory + '/' + repository_name))
    if os.path.isdir(repository_folder_path):
        # real_repository_folder_path = repository_folder_path

        for sub_folder in os.listdir(repository_folder_path):
            if 'metadatablocks' in sub_folder:
                metadatablock_folder_path = str(Path(repository_folder_path + '/' + sub_folder))

        # Open each .json file
        for metadatablock_file in os.listdir(metadatablock_folder_path):
            metadatablock_name_version = metadatablock_file

            # Get only the metadatablock name from the name of each metadatablock JSON file
            metadatablock_name = re.search(r'^([^()])+', metadatablock_name_version).group()
            metadatablock_name = metadatablock_name.rstrip('_')

            metadatablock_file_path = str(Path(metadatablock_folder_path + '/' + metadatablock_file))

            with open(metadatablock_file_path, 'r') as f:  # Open file in read mode
                metadatablock_data = f.read()  # Copy content to dataset_metadata variable
                metadatablock_data = json.loads(metadatablock_data)  # Load content as a python dict

                # Get the names of fields that have childfields
                compoundfields = []
                for parentfield in metadatablock_data['data']['fields']:
                    properties = metadatablock_data['data']['fields'][parentfield]
                    for property in properties:
                        if 'childFields' in properties:
                            field = properties[property]
                            compoundfields.append(field)
                            break

                all_parent_and_child_fields = []
                for parentfield in compoundfields:
                    if parentfield in metadatablock_data['data']['fields']:
                        properties = metadatablock_data['data']['fields'][parentfield]['childFields']
                        all_parent_and_child_fields.append(parentfield)
                        for subfield in properties:
                            all_parent_and_child_fields.append(subfield)

                            # Add parent and child names to the CSV file
                            with open(csvfile, mode='a') as data:
                                data = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                                # Write new row
                                data.writerow([repository_name, metadatablock_name, parentfield, subfield])

                # Get the names of all fields
                all_fields = []
                for parentfield in metadatablock_data['data']['fields']:
                    properties = metadatablock_data['data']['fields'][parentfield]
                    for property in properties:
                        field = properties[property]
                        all_fields.append(field)
                        break

                # Get names of primitives fields by removing list of compound and child fields from the list of all fields
                primitive_fields = list(set(all_fields) - set(all_parent_and_child_fields))

                # Add the primitive field names to the CSV file
                for primitive_field in primitive_fields:

                    # Set subfield to an empty string so that Dataverse ingests the CSV file.
                    # (Dataverse's ingest process doesn't seem to like it when there is nothing entered in the fourth column)
                    subfield = ''
                    with open(csvfile, mode='a') as data:
                        data = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                        # Write new row
                        data.writerow([repository_name, metadatablock_name, primitive_field, subfield])
