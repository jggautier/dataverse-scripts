# Join (full outer join) CSV files in a given directory

from functools import reduce
import glob
import os
import pandas as pd
from tkinter import filedialog
from tkinter import ttk
from tkinter import *

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
    join_csv_files(joinedFileDirectory, filesTuples)
    root.destroy()


def join_csv_files(joinedFileDirectory, filesTuples):

    # Create CSV file in the directory that the user selected
    filename = os.path.join(joinedFileDirectory, 'joined.csv')

    print('Creating a dataframe for each CSV file...')

    # Create a dataframe of each CSV file in the 'all-tables' list
    dataframes = [pd.read_csv(table, sep=',') for table in filesTuples]

    # For each dataframe, set the indexes (or the common columns across the dataframes to join on)
    for dataframe in dataframes:
        dataframe.set_index(['name'], inplace=True)
        # dataframe.set_index(indexList, inplace=True)

    print('Joining dataframes into one dataframe...')

    # Full outer join all dataframes and save to the 'joined' variable
    joined = reduce(lambda left, right: left.join(right, how='outer'), dataframes)

    print('Exporting joined dataframe to a CSV file...')

    # Export joined dataframe to a CSV file
    joined.to_csv(filename)

    print('Joined dataframe exported to %s' % (filename))


# Create and place frame for field for choosing CSV files
panedWindowgetCsvFiles = PanedWindow(root, borderwidth=0)
panedWindowgetCsvFiles.grid(sticky='w', row=0, padx=10, pady=5)

# Create label for button to browse for directory containing CSV files
label_getCsvFiles = Label(panedWindowgetCsvFiles, text='Choose CSV files to join:', anchor='w')
label_getCsvFiles.grid(sticky='w', row=0, pady=2)

# Create button to browse for directory containing JSON files
button_getCsvFiles = ttk.Button(panedWindowgetCsvFiles, text='Browse', command=lambda: retrieve_csv_files())
button_getCsvFiles.grid(sticky='w', row=1)

# Create and place frame for field for choosing directory for storing joined file
panedWindowjoinedFileDirectory = PanedWindow(root, borderwidth=0)
panedWindowjoinedFileDirectory.grid(sticky='w', row=1, padx=10, pady=5)

# Create label for button to browse for directory to add CSV files in
label_joinedFileDirectory = Label(panedWindowjoinedFileDirectory, text='Choose folder to store the joined CSV file:', anchor='w')
label_joinedFileDirectory.grid(sticky='w', row=0, pady=2)

# Create button to browse for directory containing JSON files
button_joinedFileDirectory = ttk.Button(panedWindowjoinedFileDirectory, text='Browse', command=lambda: retrieve_joinedfiledirectory())
button_joinedFileDirectory.grid(sticky='w', row=1)

# Create and place frame for Join button
panedWindowJoinButton = PanedWindow(root, borderwidth=0)
panedWindowJoinButton.grid(sticky='w', row=2, padx=10, pady=5)

# Create join button
button_Join = ttk.Button(panedWindowJoinButton, text='Join CSV files', command=lambda: start())
button_Join.grid(sticky='w', row=0, pady=10)

mainloop()
