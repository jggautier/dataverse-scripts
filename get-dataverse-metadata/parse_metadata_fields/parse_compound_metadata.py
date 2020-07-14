# For each dataset listed in dataset_pids.txt, get the values of given subfields of a compound metadata field

import csv
import json
import glob
import os
from pathlib import Path
import requests
from tkinter import filedialog
from tkinter import ttk
from tkinter import *

# Enter database names of parent compound fields, e.g. author, and their subfields, e.g. authorName...
compoundfields = {
    'otherId': ['otherIdAgency', 'otherIdValue'],
    'author': ['authorName', 'authorAffiliation', 'authorIdentifierScheme', 'authorIdentifier'],
    'datasetContact': ['datasetContactName', 'datasetContactAffiliation', 'datasetContactEmail'],
    'dsDescription': ['dsDescriptionValue', 'dsDescriptionDate'],
    'keyword': ['keywordValue', 'keywordVocabulary', 'keywordVocabularyURI'],
    'topicClassification': ['topicClassValue', 'topicClassVocab', 'topicClassVocabURI'],
    'publication': ['publicationCitation', 'publicationIDType', 'publicationIDNumber', 'publicationURL'],
    'producer': ['producerName', 'producerAffiliation', 'producerAbbreviation', 'producerURL', 'producerLogoURL'],
    'contributor': ['contributorType', 'contributorName'],
    'grantNumber': ['grantNumberAgency', 'grantNumberValue'],
    'distributor': ['distributorName', 'distributorAffiliation', 'distributorAbbreviation', 'distributorURL', 'distributorLogoURL'],
    'timePeriodCovered': ['timePeriodCoveredStart', 'timePeriodCoveredEnd'],
    'dateOfCollection': ['dateOfCollectionStart', 'dateOfCollectionEnd'],
    'series': ['seriesName', 'seriesInformation'],
    'software': ['softwareName', 'softwareVersion']
}

# Create GUI for getting user input

# Create, title and size the window
window = Tk()
window.title('Get compound field metadata')
window.geometry('550x250')  # width x height


# Function called when Browse button is pressed to get folder of JSON files
def retrieve_jsondirectory():
    global jsonDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    jsonDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + jsonDirectory, anchor='w', foreground='green')
    label_showChosenDirectory.grid(sticky='w', column=0, row=2)


# Function called when Browse button is pressed to get CSV file
def retrieve_csvdirectory():
    global csvDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    csvDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + csvDirectory, anchor='w', foreground='green')
    label_showChosenDirectory.grid(sticky='w', column=0, row=6)


# Function called when Start button is pressed
def start():
    window.destroy()


# Create label for button to browse for directory containing JSON files
label_getJSONFiles = Label(window, text='Choose folder containing the JSON files:', anchor='w')
label_getJSONFiles.grid(sticky='w', column=0, row=0, pady=2)

# Create button to browse for directory containing JSON files
button_getJSONFiles = ttk.Button(window, text='Browse', command=lambda: retrieve_jsondirectory())
button_getJSONFiles.grid(sticky='w', column=0, row=1)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(3, minsize=25)

# Create label for button to browse for directory to add csv files in
label_tablesDirectory = Label(window, text='Choose folder to store the csv files:', anchor='w')
label_tablesDirectory.grid(sticky='w', column=0, row=4, pady=2)

# Create button to browse for directory containing JSON files
button_tablesDirectory = ttk.Button(window, text='Browse', command=lambda: retrieve_csvdirectory())
button_tablesDirectory.grid(sticky='w', column=0, row=5)

# Create start button
button_Start = ttk.Button(window, text='Start', command=lambda: start())
button_Start.grid(sticky='w', column=0, row=7, pady=40)

# Keep window open until it's closed
mainloop()


def getsubfields(parent_compound_field, subfield):
    try:
        for fields in dataset_metadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
            if fields['typeName'] == parent_compound_field:  # Find compound name
                subfield = fields['value'][index][subfield]['value']  # Find value in subfield
    except KeyError:
        subfield = ''
    return subfield


for parent_compound_field in compoundfields:
    subfields = compoundfields[parent_compound_field]

    # Create table in directory user chose
    filename = '%s.csv' % (parent_compound_field)
    filepath = os.path.join(csvDirectory, filename)

    print('\nCreating CSV file for %s metadata' % (parent_compound_field))

    # Create column names for the header row
    ids = ['dataset_id', 'persistentUrl']
    header_row = ids + subfields

    with open(filepath, mode='w') as metadatafile:
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
            for fields in dataset_metadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
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
                            with open(filepath, mode='a') as metadatafile:

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
