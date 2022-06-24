import csv
import os
import requests
import time
from tkinter import filedialog
from tkinter import ttk
from tkinter import *
import xmltodict

####################################################################################

# Create GUI for getting user input

window = Tk()
window.title('Get record IDs in OAI-PMH feed')
window.geometry('625x450')  # width x height


# Function called when Browse button is pressed
def retrieve_directory():
    global directory

    # Call the OS's file directory window and store selected object path as a global variable
    directory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(window, text='You chose: ' + directory, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showChosenDirectory.grid(sticky='w', column=0, row=14, padx=20)


# Function called when Start button is pressed
def retrieve_input():
    global baseUrl
    global oaiSet

    # Store what's entered in dataverseUrl text box as a global variable
    baseUrl = entry_baseUrl.get().strip()

    # Store what's entered in dataverseUrl text box as a global variable
    oaiSet = entry_oaiSet.get().strip()

    if baseUrl:
        window.destroy()

    # If no baseUrl is entered, display message that one is required
    else:
        print('A dataverse URL is required')
        label_baseUrlReqiured = Label(window, text='The repository\'s OAI-PMH URL is required.', foreground='red', anchor='w')
        label_baseUrlReqiured.grid(sticky='w', column=0, row=3, padx=20)


# Create label for BaseUrl field
label_baseUrl = Label(window, text='OAI-PMH Base URL:', anchor='w')
label_baseUrl.grid(sticky='w', column=0, row=0, padx=20)

# Create Base URL field
dataverseUrl = str()
entry_baseUrl = Entry(window, width=50, textvariable=dataverseUrl)
entry_baseUrl.grid(sticky='w', column=0, row=1, pady=2, padx=20)

# Create help text for BaseUrl field
label_dataverseUrlHelpText = Label(window, text='Example: https://demo.dataverse.org/oai', foreground='grey', anchor='w')
label_dataverseUrlHelpText.grid(sticky='w', column=0, row=2, padx=20)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(4, minsize=25)

# Create label for oaiSet key field
label_oaiSet = Label(window, text='OAI set name:', anchor='w')
label_oaiSet.grid(sticky='w', column=0, row=8, padx=20)

# Create oaiSet field
oaiSet = str()
entry_oaiSet = Entry(window, width=50, textvariable=oaiSet)
entry_oaiSet.grid(sticky='w', column=0, row=9, pady=2, padx=20)

# Create help text for oaiSet field
label_oaiSetHelpText = Label(window, text='If no OAI Set is entered, all records in the repository\'s OAI-PMH feed will be retrived', foreground='grey', anchor='w')
label_oaiSetHelpText.grid(sticky='w', column=0, row=10, padx=20)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(11, minsize=25)

# Create label for Browse directory button
label_browseDirectory = Label(window, text='Choose folder to store CSV file with identifiers and statuses of harvested records:', anchor='w')
label_browseDirectory.grid(sticky='w', column=0, row=12, pady=2, padx=20)

# Create Browse directory button
button_browseDirectory = ttk.Button(window, text='Browse', command=lambda: retrieve_directory())
button_browseDirectory.grid(sticky='w', column=0, row=13, padx=20)

# Create start button
button_Submit = ttk.Button(window, text='Start', command=lambda: retrieve_input())
button_Submit.grid(sticky='w', column=0, row=15, pady=40, padx=20)

# Keep window open until it's closed
mainloop()

def improved_get(_dict, path, default=None):
    for key in path.split('.'):
        try:
            _dict = _dict[key]
        except KeyError:
            return default
    return str(_dict)


currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')
metadataPrefix = 'oai_dc'

if oaiSet:
    oaiUrl = f'{baseUrl}?verb=ListIdentifiers&set={oaiSet}&metadataPrefix={metadataPrefix}'
else:
    oaiSet = 'no_set'
    oaiUrl = f'{baseUrl}?verb=ListIdentifiers&metadataPrefix={metadataPrefix}'

csvFile = f'harvested_records_{oaiSet}_{currentTime}.csv'
csvFilePath = os.path.join(directory, csvFile)

print('Counting current and deleted records:')

response = requests.get(oaiUrl)
dictData = xmltodict.parse(response.content)

recordCount = 0
deletedRecordCount = 0

with open(csvFilePath, mode='w', encoding='utf-8', newline='') as f:
    f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    f.writerow(['record_identifier', 'record_status'])

    if 'resumptionToken' not in dictData['OAI-PMH']['ListIdentifiers']:
        for record in dictData['OAI-PMH']['ListIdentifiers']['header']:
            recordIdentifier = record['identifier']
            recordStatus = record.get('@status')
            if recordStatus != 'deleted':
                recordStatus = 'present'
                recordCount += 1
            elif recordStatus == 'deleted':
                deletedRecordCount +=1

            f.writerow([recordIdentifier, recordStatus])

        print(f'Record count in {oaiSet} set: {recordCount}')
        print(f'Count of deleted records: {deletedRecordCount}')

    elif 'resumptionToken' in dictData['OAI-PMH']['ListIdentifiers']:
        pageCount = 1
        print(f'Counting records in page {pageCount}', end='\r', flush=True)

        resumptionToken = improved_get(dictData, 'OAI-PMH.ListIdentifiers.resumptionToken.#text')

        for record in dictData['OAI-PMH']['ListIdentifiers']['header']:
            recordIdentifier = record['identifier']
            recordStatus = record.get('@status')
            if recordStatus != 'deleted':
                recordStatus = 'present'
                recordCount += 1
            elif recordStatus == 'deleted':
                deletedRecordCount +=1

            f.writerow([recordIdentifier, recordStatus])

            resumptionToken = improved_get(dictData, 'OAI-PMH.ListIdentifiers.resumptionToken.#text')

        while resumptionToken is not None:
            pageCount += 1
            print(f'Counting records in page {pageCount}', end='\r', flush=True)

            oaiUrlResume = f'{baseUrl}?verb=ListIdentifiers&resumptionToken={resumptionToken}'
            response = requests.get(oaiUrlResume)
            dictData = xmltodict.parse(response.content)

            for record in dictData['OAI-PMH']['ListIdentifiers']['header']:
                recordIdentifier = record['identifier']
                recordStatus = record.get('@status')
                if recordStatus != 'deleted':
                    recordStatus = 'present'
                    recordCount += 1
                elif recordStatus == 'deleted':
                    deletedRecordCount +=1

                f.writerow([recordIdentifier, recordStatus])

            resumptionToken = improved_get(dictData, 'OAI-PMH.ListIdentifiers.resumptionToken.#text')

        if oaiSet != 'no_set':
            print(f'\nRecord count in {oaiSet} set: {recordCount}')
        else:
            print(f'\nRecord count: {recordCount}')
        print(f'Count of deleted records: {deletedRecordCount}')
        print(f'Record identifiers saved to {csvFilePath}')
