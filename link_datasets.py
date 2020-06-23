# Script for creating links to datasets in a given text file
# into a given dataverse

import os
import requests
from tkinter import filedialog
from tkinter import *
from urllib.parse import urlparse

# Ask user for file containing dataset/dataverse IDs
print('Choose a text file with database IDs of the datasets/dataverses to link\
 or unlink:')

# Open window to let user select file from her OS, save file path and openfile command as variables
toplevel = Tk()
toplevel.withdraw()
# toplevel.update()
filename = filedialog.askopenfilename()
openfile = open(filename)

total = len(open(filename).readlines())  # Save total number of IDs (lines) in file as $total.

# To-do: See if the API endpoint will except dataset PIDs instead of database IDs.
# To-do: Check if file has at least one line, or print that file is empty and re-ask for file.

# Ask user for url of dataverse to link into
dataverse_url = raw_input('\n' + 'Enter full URL of dataverse to add links to,\
 e.g. http(s)://demo.dataverse.org/dataverse/mydataverse:')  # e.g. demo

# Parse url to get server name and alias
parsed = urlparse(dataverse_url)
server = parsed.scheme + '://' + parsed.netloc
alias = parsed.path.split('/')[2]

# To-do: If there's a parsing error, print that the URL entered was incorrect and re-ask for URL.

# Ask user for superuser API token
token = raw_input('\n' + 'Paste superuser API token:')

# Ask user if they're linking or unlinking
mode = raw_input('\n' + 'Type 1 to link or type 2 to unlink:')
if mode == '1':
    mode = 'link'
    print('You typed 1 to link.')

    # Ask user if they're linking datasets or dataverses
    object = raw_input('\n' + 'Type 1 to link datasets or type 2 to link dataveres:')
    if object == '1':
        object = 'datasets'
        print('\n' + 'Linking datasets in %s...' % (alias))
        # To-do: Wait for user to press Enter/Return

        # Run script for linking datasets
        if os.path.isfile(filename):
            start = 0
            # total = len(open(filename).readlines()) # Save total number of IDs (lines) in file as $total.

            for database_id in openfile:
                database_id = database_id.strip()
                url_add_link = '%s/api/datasets/%s/link/%s' % (server, database_id, alias)  # Add link to dataverse
                r = requests.put(url_add_link, headers={'X-Dataverse-key': token})  # Add link to dataverse

                # To-do: Check request status, and report if API failed and which dataset ID it failed on.

                print('Datasets linked: %s of total: %s' % (start, total))
                start += 1
            print('Datasets linked: %s of total: %s' % (total, total))

    elif object == '2':
        object = 'dataverses'
        print('\n' + 'Linking dataverses in %s...' % (alias))
        # To-do: Wait for user to press Enter/Return

        # Run script for linking dataverses
        if os.path.isfile(filename):
            start = 0
            # total = len(open(filename).readlines()) # Save total number of IDs (lines) in file as $total.

            for database_id in openfile:
                database_id = database_id.strip()
                url_add_link = '%s/api/dataverses/%s/link/%s' % (server, database_id, alias)  # Add link to dataverse
                r = requests.put(url_add_link, headers={'X-Dataverse-key': token})  # Add link to dataverse

                print('Dataverses linked: %s of total: %s' % (start, total))
                start += 1
            print('Dataverses linked: %s of total: %s' % (total, total))


elif mode == '2':
    mode = 'deleteLink'
    # Ask user if they're unlinking datasets or dataverses
    object = raw_input('\n' + 'Type 1 to unlink datasets or type 2 to unlink dataveres:')
    if object == '1':
        object = 'datasets'
        print('\n' + 'Unlinking datasets in %s...' % (alias))
        # To-do: Wait for user to press Enter/Return

        # Run script for unlinking datasets
        if os.path.isfile(filename):
            start = 0
            # total = len(open(filename).readlines()) # Save total number of IDs (lines) in file as $total.

            for database_id in openfile:
                database_id = database_id.strip()
                url_delete_link = '%s/api/datasets/%s/deleteLink/%s' % (server, database_id, alias)  # Remove link from a dataverse
                r = requests.delete(url_delete_link, headers={'X-Dataverse-key': token})  # Remove link from a dataverse
                print('Datasets unlinked: %s of total: %s' % (start, total))
                start += 1
            print('Datasets linked: %s of total: %s' % (total, total))

    elif object == '2':
        object = 'dataverses'
        print('\n' + 'Unlinking dataverses in %s...' % (alias))
        # To-do: Wait for user to press Enter/Return

        # Run script for unlinking datasets
        if os.path.isfile(filename):
            start = 0
            # total = len(open(filename).readlines()) # Save total number of IDs (lines) in file as $total.

            for database_id in openfile:
                database_id = database_id.strip()
                url_delete_link = '%s/api/dataverses/%s/deleteLink/%s' % (server, database_id, alias)  # Remove link from a dataverse
                r = requests.delete(url_delete_link, headers={'X-Dataverse-key': token})  # Remove link from a dataverse
                print('Dataverses unlinked: %s of total: %s' % (start, total))
                start += 1
            print('Datasets linked: %s of total: %s' % (total, total))
