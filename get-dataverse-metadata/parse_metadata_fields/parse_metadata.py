# For each dataset listed in dataset_pids.csv, get the values of any fields that are primitive (don't have subfields)

import csv
import json
import glob
import os
from pathlib import Path
from tkinter import filedialog
from tkinter import ttk
from tkinter import *

# Create GUI for getting user input

# Create, title and size the window
window = Tk()
window.title('Get metadata from primitive fields')
window.geometry('600x400')  # width x height


# Function called when user presses the browse button to choose the metadatablock file
def retrieve_metadatablockfile():
    global metadatablockfile

    # Call the OS's file directory window and store selected object path as a global variable
    metadatablockfile = filedialog.askopenfilename(filetypes=[('JSON file', '*.json')])

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + metadatablockfile, anchor='w', foreground='green')
    label_showChosenDirectory.grid(sticky='w', column=0, row=2)


# Function called when user presses the browse button to choose the folder containing the JSON metadata files
def retrieve_jsondirectory():
    global jsonDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    jsonDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + jsonDirectory, anchor='w', foreground='green')
    label_showChosenDirectory.grid(sticky='w', column=0, row=6)


# Function called when user presses the browse button to choose the folder to add the CSV files to
def retrieve_csvdirectory():
    global csvDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    csvDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + csvDirectory, anchor='w', foreground='green')
    label_showChosenDirectory.grid(sticky='w', column=0, row=10)


# Function called when Browse button is pressed
def start():
    window.destroy()


# Create label for button to browse for the JSON file containing metadatablock information
label_getMetadatablockFile = Label(window, text='Choose metadatablock JSON file:', anchor='w')
label_getMetadatablockFile.grid(sticky='w', column=0, row=0, pady=2)

# Create button to browse for JSON file containing metadatablock information
button_getMetadatablockFile = ttk.Button(window, text='Browse', command=lambda: retrieve_metadatablockfile())
button_getMetadatablockFile.grid(sticky='w', column=0, row=1)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(3, minsize=25)

# Create label for button to browse for directory containing JSON files
label_getJSONFiles = Label(window, text='Choose folder containing the JSON metadata files:', anchor='w')
label_getJSONFiles.grid(sticky='w', column=0, row=4, pady=2)

# Create button to browse for directory containing JSON metadata files
button_getJSONFiles = ttk.Button(window, text='Browse', command=lambda: retrieve_jsondirectory())
button_getJSONFiles.grid(sticky='w', column=0, row=5)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(7, minsize=25)

# Create label for button to browse for directory to add csv files in
label_tablesDirectory = Label(window, text='Choose folder to store the folder of CSV files:', anchor='w')
label_tablesDirectory.grid(sticky='w', column=0, row=8, pady=2)

# Create button to browse for directory containing JSON files
button_tablesDirectory = ttk.Button(window, text='Browse', command=lambda: retrieve_csvdirectory())
button_tablesDirectory.grid(sticky='w', column=0, row=9)

# Create start button
button_Start = ttk.Button(window, text='Start', command=lambda: start())
button_Start.grid(sticky='w', column=0, row=11, pady=40)

# Keep window open until it's closed
mainloop()


# Read metadatablock file
with open(metadatablockfile, 'r') as f:  # Open file in read mode
    metadatablock_data = f.read()  # Copy content to a variable
    metadatablock_data = json.loads(metadatablock_data)  # Resave content as a python dict

    # Get name of metadatablock from metadatablock file
    metadatablock_name = metadatablock_data['data']['name']

    # Get the names of fields that have childfields
    compoundfields = []
    for parent_compound_field in metadatablock_data['data']['fields']:
        properties = metadatablock_data['data']['fields'][parent_compound_field]
        for property in properties:
            if 'childFields' in properties:
                field = properties[property]
                compoundfields.append(field)
                break

# Create a dictionary containing the names of the compound fields and their child fields
compound_field_dictionary = {}
all_parent_and_child_fields = []
for parentfield in compoundfields:
    if parentfield in metadatablock_data['data']['fields']:
        properties = metadatablock_data['data']['fields'][parentfield]['childFields']
        all_parent_and_child_fields.append(parentfield)
        subfields = []
        for subfield in properties:
            all_parent_and_child_fields.append(subfield)
            subfields.append(subfield)
            compound_field_dictionary[parentfield] = subfields

    all_parent_and_child_fields = []
    for parent_compound_field in compoundfields:
        if parent_compound_field in metadatablock_data['data']['fields']:
            properties = metadatablock_data['data']['fields'][parent_compound_field]['childFields']
            all_parent_and_child_fields.append(parent_compound_field)
            for subfield in properties:
                all_parent_and_child_fields.append(subfield)


def getsubfields(parent_compound_field, subfield):
    try:
        for fields in dataset_metadata['data']['latestVersion']['metadataBlocks'][metadatablock_name]['fields']:
            if fields['typeName'] == parent_compound_field:  # Find compound name
                subfield = fields['value'][index][subfield]['value']  # Find value in subfield
    except KeyError:
        subfield = ''
    return subfield


for parent_compound_field in compound_field_dictionary:
    subfields = compound_field_dictionary[parent_compound_field]

    # Create table in directory user chose
    compound_field_csv_filename = '%s.csv' % (parent_compound_field)
    compound_field_csv_filepath = os.path.join(csvDirectory, compound_field_csv_filename)

    print('\nCreating CSV file for %s metadata' % (parent_compound_field))

    # Create column names for the header row
    ids = ['dataset_id', 'persistentUrl']
    header_row = ids + subfields

    with open(compound_field_csv_filepath, mode='w') as metadatafile:
        metadatafile = csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        metadatafile.writerow(header_row)  # Create header row

    print('Getting %s metadata:' % (parent_compound_field))

    parseerrordatasets = []

    # For each file in a folder of json files
    for file in glob.glob(os.path.join(jsonDirectory, '*.json')):

        # Open each file in read mode
        with open(file, 'r') as f1:

            # Copy content to dataset_metadata variable
            dataset_metadata = f1.read()

            # Overwrite variable with content as a python dict
            dataset_metadata = json.loads(dataset_metadata)

        if (dataset_metadata['status'] == 'OK') and ('latestVersion' in dataset_metadata['data']):

            # Count number of the given compound fields
            for fields in dataset_metadata['data']['latestVersion']['metadataBlocks'][metadatablock_name]['fields']:
                if fields['typeName'] == parent_compound_field:  # Find compound name
                    total = len(fields['value'])

                    # If there are compound fields
                    if total:
                        index = 0
                        condition = True

                        while (condition):

                            # Save the dataset id of each dataset
                            dataset_id = str(dataset_metadata['data']['id'])

                            # Save the identifier of each dataset
                            persistentUrl = dataset_metadata['data']['persistentUrl']

                            # Save subfield values to variables
                            for subfield in subfields:
                                globals()[subfield] = getsubfields(parent_compound_field, subfield)

                            # Append fields to the csv file
                            with open(compound_field_csv_filepath, mode='a') as metadatafile:

                                # Create list of variables
                                row_variables = [dataset_id, persistentUrl]
                                for subfield in subfields:
                                    row_variables.append(globals()[subfield])

                                # Convert all characters to utf-8
                                def to_utf8(lst):
                                    return [unicode(elem).encode('utf-8') for elem in lst]

                                metadatafile = csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                                # Write new row using list of variables
                                metadatafile.writerow(row_variables)

                                # As a progress indicator, print a dot each time a row is written
                                sys.stdout.write('.')
                                sys.stdout.flush()

                            index += 1
                            condition = index < total

        else:
            parseerrordatasets.append(file)

    print('\nFinished writing %s metadata to %s' % (parent_compound_field, csvDirectory))

    if parseerrordatasets:
        parseerrordatasets = set(parseerrordatasets)
        print('The following %s JSON file(s) could not be parsed. The file(s) may be draft or deaccessioned dataset(s):' % (len(parseerrordatasets)))
        print(*parseerrordatasets, sep='\n')


# Get list of primitive fields in the given metadatablock JSON file

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

# Get metadata of the primitive fields

for primitive_field in primitive_fields:

    # Store path of CSV file to variable
    primitive_field_csv_filepath = os.path.join(csvDirectory, '%s.csv' % (primitive_field))

    with open(primitive_field_csv_filepath, mode='w') as metadatafile:
        metadatafile = csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Create header row
        metadatafile.writerow(['dataset_id', 'persistentUrl', primitive_field])

    print('\nGetting %s metadata:' % (primitive_field))

    parseerrordatasets = []

    # For each file in the folder of JSON files
    for file in glob.glob(os.path.join(jsonDirectory, '*.json')):

        # Open each file in read mode
        with open(file, 'r') as f1:

            # Copy content to dataset_metadata variable
            dataset_metadata = f1.read()

            # Overwrite variable with content as a python dict
            dataset_metadata = json.loads(dataset_metadata)

            if (dataset_metadata['status'] == 'OK') and ('latestVersion' in dataset_metadata['data']):

                # Save the dataset id of each dataset
                dataset_id = str(dataset_metadata['data']['id'])

                # Couple each field value with the dataset_id and write as a row to subjects.csv
                for fields in dataset_metadata['data']['latestVersion']['metadataBlocks'][metadatablock_name]['fields']:
                    if fields['typeName'] == primitive_field:
                        value = fields['value']

                        # Check if value is a string, which means the field doesn't allow multiple values
                        if isinstance(value, str):
                            persistentUrl = dataset_metadata['data']['persistentUrl']
                            dataset_id = str(dataset_metadata['data']['id'])

                            with open(primitive_field_csv_filepath, mode='a') as metadatafile:

                                # Convert all characters to utf-8 to avoid encoding errors when writing to the csv file
                                def to_utf8(lst):
                                    return [unicode(elem).encode('utf-8') for elem in lst]

                                metadatafile = csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                                # Write new row
                                metadatafile.writerow([dataset_id, persistentUrl, value])

                                # As a progress indicator, print a dot each time a row is written
                                sys.stdout.write('.')
                                sys.stdout.flush()

                        # Check if value is a list, which means the field allows multiple values
                        elif isinstance(value, list):
                            for value in fields['value']:
                                persistentUrl = dataset_metadata['data']['persistentUrl']
                                with open(primitive_field_csv_filepath, mode='a') as metadatafile:

                                    # Convert all characters to utf-8 to avoid encoding errors when writing to the csv file
                                    def to_utf8(lst):
                                        return [unicode(elem).encode('utf-8') for elem in lst]

                                    metadatafile = csv.writer(metadatafile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                                    # Write new row
                                    metadatafile.writerow([dataset_id, persistentUrl, value])

                                    # As a progress indicator, print a dot each time a row is written
                                    sys.stdout.write('.')
                                    sys.stdout.flush()
            else:
                parseerrordatasets.append(file)

    print('\nFinished writing %s metadata to %s' % (primitive_field, csvDirectory))

if parseerrordatasets:
    parseerrordatasets = set(parseerrordatasets)
    print('The following %s JSON file(s) could not be parsed. It/they may be draft or deaccessioned dataset(s):' % (len(parseerrordatasets)))
    print(*parseerrordatasets, sep='\n')

# Delete any CSV files that are empty and report
deletedfiles = []
for file in glob.glob(os.path.join(csvDirectory, '*.csv')):
    with open(file, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        data = list(reader)
        row_count = len(data) - 1
        if row_count == 0:
            filename = Path(file).name
            deletedfiles.append(filename)
            os.remove(file)
if deletedfiles:
    print('\n%s files have no metadata and were deleted:' % (len(deletedfiles)))
    print(deletedfiles)
