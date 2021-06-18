# Python script for getting the Dataverse collection names of given dataset PIDs

import csv
from csv import DictReader
import os
import requests
from tkinter import *
from tkinter import filedialog
from tkinter import ttk

# Create GUI for getting user input
window = Tk()
window.title('Get Dataverse collection names')
window.geometry('500x600')  # width x height

# Create label for Dataverse repository URL
label_repositoryURL = Label(window, text='Enter Dataverse repository URL:', anchor='w')
label_repositoryURL.grid(sticky='w', column=0, row=0)

# Create Dataverse repository URL text box
repositoryURL = str()
entry_repositoryURL = Entry(window, width=50, textvariable=repositoryURL)
entry_repositoryURL.grid(sticky='w', column=0, row=1, pady=2)

# Create help text for server name field
label_dataverseUrlHelpText = Label(window, text='Example: https://demo.dataverse.org/', foreground='grey', anchor='w')
label_dataverseUrlHelpText.grid(sticky='w', column=0, row=2)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(3, minsize=25)

# Create label for API key field
labelApikey = Label(window, text='API token/key:', anchor='w')
labelApikey.grid(sticky='w', column=0, row=4)

# Create API key field
apikey = str()
entryApikey = Entry(window, width=50, textvariable=apikey)
entryApikey.grid(sticky='w', column=0, row=5, pady=2)

# Create help text for API key field
labelApikeyHelpText = Label(window, text='If no API token/key is entered, only published metadata will be downloaded', foreground='grey', anchor='w')
labelApikeyHelpText.grid(sticky='w', column=0, row=6)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(7, minsize=25)

# Create label for Browse directory button
label_browseForFile = Label(window, text='Choose CSV or TXT file containing list of dataset PIDs:', anchor='w')
label_browseForFile.grid(sticky='w', column=0, row=8, pady=2)

# Create Browse directory button
button_browseForFile = ttk.Button(window, text='Browse', command=lambda: retrieve_file())
button_browseForFile.grid(sticky='w', column=0, row=9)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(11, minsize=25)

# Create label for Browse directory button
label_browseDirectory = Label(window, text='Choose folder to put CSV file into:', anchor='w')
label_browseDirectory.grid(sticky='w', column=0, row=12, pady=2)

# Create Browse directory button
button_browseDirectory = ttk.Button(window, text='Browse', command=lambda: retrieve_directory())
button_browseDirectory.grid(sticky='w', column=0, row=13)

# Create start button
button_Submit = ttk.Button(window, text='Start', command=lambda: retrieve_input())
button_Submit.grid(sticky='w', column=0, row=15, pady=40)


# Function called when Browse button is pressed for choosing file with dataset PIDs
def retrieve_file():
    global datasetPIDFile

    # Call the OS's file directory window and store selected object path as a global variable
    datasetPIDFile = filedialog.askopenfilename(filetypes=[('Text files', '*.txt'), ('CSV files', '*.csv')])

    # Show user which file she chose
    label_showChosenFile = Label(window, text='You chose: ' + datasetPIDFile, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showChosenFile.grid(sticky='w', column=0, row=10)


# Function called when Browse button is pressed
def retrieve_directory():
    global csvDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    csvDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + csvDirectory, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showChosenDirectory.grid(sticky='w', column=0, row=14)


# Function called when Start button is pressed
def retrieve_input():
    global repositoryURL

    # Store what's entered in dataverseUrl text box as a global variable
    repositoryURL = entry_repositoryURL.get()

    window.destroy()


# Keep window open until it's closed
mainloop()

datasetPIDs = []
if '.csv' in datasetPIDFile:
    with open(datasetPIDFile, mode='r', encoding='utf-8') as f:
        csvDictReader = DictReader(f, delimiter=',')
        for row in csvDictReader:
            datasetPIDs.append(row['persistent_id'].rstrip())

elif '.txt' in datasetPIDFile:
    datasetPIDFile = open(datasetPIDFile)
    for datasetPID in datasetPIDFile:

        # Remove any trailing spaces from datasetPID
        datasetPIDs.append(datasetPID.rstrip())

total = len(datasetPIDs)

filename = os.path.join(csvDirectory, 'dataverse_names.csv')

# Create CSV file
with open(filename, mode='w') as opencsvfile:
    opencsvfile = csv.writer(opencsvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Create header row
    opencsvfile.writerow(['persistentUrl', 'dataverseAlias', 'dataverseName'])

datasetPIDErrors = []
count = 0
for datasetPID in datasetPIDs:
    try:
        if apikey:
            url = '%s/api/search?q="%s"&type=dataset&show_entity_ids=true&key=%s' % (repositoryURL, datasetPID, apikey)
        else:
            url = '%s/api/search?q="%s"&type=dataset&show_entity_ids=true' % (repositoryURL, datasetPID)
        response = requests.get(url)
        data = response.json()

        # Save dataset PID, Dataverse name and Dataverse alias
        persistentUrl = data['data']['items'][0]['url']
        dataverseName = data['data']['items'][0]['name_of_dataverse']
        dataverseAlias = data['data']['items'][0]['identifier_of_dataverse']

        # Write values of the three variables to a new row in the CSV
        with open(filename, mode='a') as datasets:
            datasets = csv.writer(datasets, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            datasets.writerow([persistentUrl, dataverseAlias, dataverseName])
        count += 1

    except Exception:
        datasetPIDErrors.append(datasetPID)

    print('Dataverse collection names retrieved: %s of %s (%s)' % (count, total, datasetPID))
if datasetPIDErrors:
    print('The Dataverse collection names of these datasets could not be retrieved:\n')
    print(datasetPIDErrors)
