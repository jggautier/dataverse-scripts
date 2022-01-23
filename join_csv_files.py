# Join (full outer join) CSV files in a given directory

from functools import reduce
import glob
import os
import pandas as pd
from tkinter import filedialog, Label, Tk, PanedWindow, Entry, mainloop, Listbox
from tkinter import MULTIPLE, StringVar, Scrollbar, N, S, E, W
from tkmacosx import Button


# Function called when button is pressed for browsing for CSV files
def retrieve_csv_files():
    global filesList
    global columnLists

    filesList = filedialog.askopenfilenames(filetypes=[('CSV','*.csv')])

    text = 'You chose %s file(s)' % (len(filesList))

    # Show user which directory she chose
    label_showFileCount = Label(
        panedWindowgetCsvFiles, text=text, anchor='w', 
        foreground='green', wraplength=500, justify='left')
    label_showFileCount.grid(sticky='w', row=2)

    # Get names of columns that exist in all chosen CSV files
    dataframes = [pd.read_csv(table, sep=',') for table in filesList]
    columnLists = []
    for dataframe in dataframes:
        columnLists.append(dataframe.columns)
    commonColumns = list(reduce(set.intersection, map(set, columnLists)))

    # Add names of common columns to list box
    values.set(commonColumns)

# Function called when button is pressed for browsing for folder to save joined CSV file
def retrieve_joinedfiledirectory():
    global joinedFileDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    joinedFileDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(
        panedWindowjoinedFileDirectory, 
        text='You chose: ' + joinedFileDirectory, anchor='w', 
        foreground='green', wraplength=500, justify='left')
    label_showChosenDirectory.grid(sticky='w', row=2)


# Function for joining the given CSV files
def join_csv_files(filesList, indexList, joinedFileDirectory):

    # Create CSV file in the directory that the user selected
    filename = os.path.join(joinedFileDirectory, 'joined.csv')

    print('Creating a dataframe for each CSV file...')

    # Create a dataframe of each CSV file in the 'filesList' list
    dataframes = [pd.read_csv(table, sep=',', na_filter = False) for table in filesList]

    # For each dataframe, set the indexes (or the common columns across the dataframes to join on)
    for dataframe in dataframes:
        dataframe.set_index(indexList, inplace=True)
        # dataframe.set_index(indexList, inplace=True)

    print('Joining dataframes into one dataframe...')

    # Full outer join all dataframes and save to the 'joined' variable
    joined = reduce(lambda left, right: left.join(right, how='outer'), dataframes)

    print('Exporting joined dataframe to a CSV file...')

    # Export joined dataframe to a CSV file
    joined.to_csv(filename)

    print('Joined dataframe exported to %s' % (filename))


# Function called when button is pressed to join given CSV files
def join():
    # Get columns user chose from listbox
    selectedColumns = []
    selections = listBox_chooseColumns.curselection()
    for selection in selections:
        column = listBox_chooseColumns.get(selection)
        selectedColumns.append(column)

    try:
        join_csv_files(filesList, selectedColumns, joinedFileDirectory)
        root.destroy()
    except Exception as e:
        e = str(e)
        if e == 'name \'filesList\' is not defined' or\
            e == 'are in the columns' in e or\
            e == 'name \'joinedFileDirectory\' is not defined' or\
            e == 'reduce() of empty sequence with no initial value':

            error = 'Check your entries and try again.'
        else:
            error = e

        label_Error = Label(
            panedWindowJoinButton,
            text=error,
            foreground='red')
        label_Error.grid(sticky='w', row=1)


# Create GUI for getting user input

# Create and title of the root main window
root = Tk()
root.title('Join CSV files (full outer join)')

# Create frames
panedWindowgetCsvFiles = PanedWindow(root, borderwidth=0)
panedWindowgetIndexes = PanedWindow(root, borderwidth=0)
panedWindowjoinedFileDirectory = PanedWindow(root, borderwidth=0)
panedWindowJoinButton = PanedWindow(root, borderwidth=0)

# Create label for button to browse for directory containing CSV files
label_getCsvFiles = Label(
    panedWindowgetCsvFiles, 
    text='Choose CSV files to join', anchor='w')
label_getCsvFiles.grid(sticky='w', row=0)

# Create button to browse for directory containing JSON files
button_getCsvFiles = Button(
    panedWindowgetCsvFiles, text='Browse', 
    command=lambda: retrieve_csv_files())
button_getCsvFiles.grid(sticky='w', row=1)

# Create label for text box for entering names of columns to join on
label_getIndexes = Label(
    panedWindowgetIndexes, 
    text='Choose column names to join on', anchor='w')
label_getIndexes.grid(sticky='w', row=0)

# Create Listbox for choosing columns to join on
values = StringVar()
listBox_chooseColumns = Listbox(panedWindowgetIndexes,
    width=28, height=5,
    listvariable=values, selectmode=MULTIPLE, exportselection=0)
listBox_chooseColumns.grid(sticky='w', row=1)

# Add scroll bar to Listbox for choosing columns to join on
scrollbar = Scrollbar(panedWindowgetIndexes, orient='vertical')
scrollbar.config(command=listBox_chooseColumns.yview)
scrollbar.grid(column=1, row=1, sticky=N+S+W)
listBox_chooseColumns.config(yscrollcommand=scrollbar.set)

# Create label for button to browse for directory to add CSV files in
label_joinedFileDirectory = Label(
    panedWindowjoinedFileDirectory, 
    text='Choose folder to save the joined CSV file in', anchor='w')
label_joinedFileDirectory.grid(sticky='w', row=0)

# Create button to browse for directory containing JSON files
button_joinedFileDirectory = Button(
    panedWindowjoinedFileDirectory, 
    text='Browse', command=lambda: retrieve_joinedfiledirectory())
button_joinedFileDirectory.grid(sticky='w', row=1)

# Create join button
button_Join = Button(
    panedWindowJoinButton, text='Join CSV files', 
    width=150, height=40, fg='white', bg='blue',
    command=lambda: join())
button_Join.grid(sticky='w', row=0)

# Place frames
panedWindowgetCsvFiles.grid(sticky='w', row=0, padx=10, pady=10)
panedWindowgetIndexes.grid(sticky='w', row=1, padx=10, pady=10)
panedWindowjoinedFileDirectory.grid(sticky='w', row=2, padx=10, pady=10)
panedWindowJoinButton.grid(sticky='w', row=3, padx=10, pady=10)

mainloop()
