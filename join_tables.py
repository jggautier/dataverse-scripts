# Join (full outer join) CSV files in a given directory

from functools import reduce
import glob
import os
import pandas as pd
from tkinter import *
from tkinter import messagebox, filedialog

# Create GUI for getting user input

# Create, title and size the root
root = Tk()
root.title('Join CSV files')


# Function called when Browse button is pressed
def retrieve_csv_files():
    global filesTuples

    filesTuples = filedialog.askopenfilenames(filetypes=[('CSV','*.csv')])

    text = 'You chose %s file(s)' % (len(filesTuples))

    # Show user which directory she chose
    label_showFileCount = Label(panedWindowgetCsvFiles, text=text, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showFileCount.grid(sticky='w', row=2)


# Function called when Browse button is pressed
def retrieve_joinedfiledirectory():
    global joinedFileDirectory

    # Call the OS's file directory window and store selected object path as a global variable
    joinedFileDirectory = filedialog.askdirectory()

    # Show user which directory she chose
    label_showChosenDirectory = Label(panedWindowjoinedFileDirectory, text='You chose: ' + joinedFileDirectory, anchor='w', foreground='green', wraplength=500, justify='left')
    label_showChosenDirectory.grid(sticky='w', row=2)


# Function called when Browse button is pressed
def start():
    indexString = entry_getIndexes.get()
    indexList = [x.strip() for x in indexString.split(',')]

    join_csv_files(joinedFileDirectory, filesTuples, indexList)
    root.destroy()


def join_csv_files(joinedFileDirectory, filesTuples, indexList):

    # Create CSV file in the directory that the user selected
    filename = os.path.join(joinedFileDirectory, 'joined.csv')

    print('Creating a dataframe for each CSV file...')

    # Create a dataframe of each CSV file in the 'all-tables' list
    dataframes = [pd.read_csv(table, sep=',') for table in filesTuples]

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


# Create frames
panedWindowgetCsvFiles = PanedWindow(root, borderwidth=0)
panedWindowgetIndexes = PanedWindow(root, borderwidth=0)
panedWindowjoinedFileDirectory = PanedWindow(root, borderwidth=0)
panedWindowJoinButton = PanedWindow(root, borderwidth=0)

# Create label for button to browse for directory containing CSV files
label_getCsvFiles = Label(panedWindowgetCsvFiles, text='Choose CSV files to join', anchor='w')
label_getCsvFiles.grid(sticky='w', row=0)

# Create button to browse for directory containing JSON files
button_getCsvFiles = Button(panedWindowgetCsvFiles, text='Browse', command=lambda: retrieve_csv_files())
button_getCsvFiles.grid(sticky='w', row=1)

# Create label for text box for entering names of columns to join on
label_getIndexes = Label(panedWindowgetIndexes, text='Enter columns to join on', anchor='w')
label_getIndexes.grid(sticky='w', row=0)

# Create text box for entering names of columns to join on
entry_getIndexes = Entry(panedWindowgetIndexes, width=30)
entry_getIndexes.grid(sticky='w', row=1)

# Create label for text box for entering names of columns to join on
label_getIndexesHelpText = Label(panedWindowgetIndexes, text='Separate column names with commas', foreground='grey', anchor='w')
label_getIndexesHelpText.grid(sticky='w', row=2)

# Create label for button to browse for directory to add CSV files in
label_joinedFileDirectory = Label(panedWindowjoinedFileDirectory, text='Choose folder to save the joined CSV file in', anchor='w')
label_joinedFileDirectory.grid(sticky='w', row=0)

# Create button to browse for directory containing JSON files
button_joinedFileDirectory = Button(panedWindowjoinedFileDirectory, text='Browse', command=lambda: retrieve_joinedfiledirectory())
button_joinedFileDirectory.grid(sticky='w', row=1)

# Create join button
button_Join = Button(panedWindowJoinButton, text='Join CSV files', command=lambda: start())
button_Join.grid(sticky='w', row=0)

# Place frames
panedWindowgetCsvFiles.grid(sticky='w', row=0, padx=10, pady=10)
panedWindowgetIndexes.grid(sticky='w', row=1, padx=10, pady=10)
panedWindowjoinedFileDirectory.grid(sticky='w', row=2, padx=10, pady=10)
panedWindowJoinButton.grid(sticky='w', row=3, padx=10, pady=10)

mainloop()
