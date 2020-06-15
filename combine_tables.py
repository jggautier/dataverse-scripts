# Join (full outer join) csv files in a given directory

from functools import reduce
import glob
import os
import pandas as pd
from tkinter import filedialog
from tkinter import ttk
from tkinter import *

# Create GUI for getting user input

# Create, title and size the window
window = Tk()
window.title('Join csv files')
window.geometry('550x250')  # width x height


# Function called when Browse button is pressed
def retrieve_csvdirectory():
	global csvDirectory

	# Call the OS's file directory window and store selected object path as a global variable
	csvDirectory = filedialog.askdirectory()

	# Show user which directory she chose
	label_showChosenDirectory = Label(window, text='You chose: ' + csvDirectory, anchor='w', foreground='green')
	label_showChosenDirectory.grid(sticky='w', column=0, row=2)


# Function called when Browse button is pressed
def retrieve_mergedfiledirectory():
	global mergedFileDirectory

	# Call the OS's file directory window and store selected object path as a global variable
	mergedFileDirectory = filedialog.askdirectory()

	# Show user which directory she chose
	label_showChosenDirectory = Label(window, text='You chose: ' + mergedFileDirectory, anchor='w', foreground='green')
	label_showChosenDirectory.grid(sticky='w', column=0, row=6)


# Function called when Browse button is pressed
def start():
	window.destroy()


# Create label for button to browse for directory containing JSON files
label_getCsvFiles = Label(window, text='Choose folder containing the CSV files to join:', anchor='w')
label_getCsvFiles.grid(sticky='w', column=0, row=0, pady=2)

# Create button to browse for directory containing JSON files
button_getCsvFiles = ttk.Button(window, text='Browse', command=lambda: retrieve_csvdirectory())
button_getCsvFiles.grid(sticky='w', column=0, row=1)

# Create empty row in grid to improve spacing between the two fields
window.grid_rowconfigure(3, minsize=25)

# Create label for button to browse for directory to add csv files in
label_mergedFileDirectory = Label(window, text='Choose folder to store the csv file:', anchor='w')
label_mergedFileDirectory.grid(sticky='w', column=0, row=4, pady=2)

# Create button to browse for directory containing JSON files
button_mergedFileDirectory = ttk.Button(window, text='Browse', command=lambda: retrieve_mergedfiledirectory())
button_mergedFileDirectory.grid(sticky='w', column=0, row=5)

# Create start button
button_Start = ttk.Button(window, text='Start', command=lambda: start())
button_Start.grid(sticky='w', column=0, row=7, pady=40)

# Keep window open until it's closed
mainloop()

directory_name = csvDirectory.split('/')[-1]

# Create csv file in the directory that the user selected
filename = os.path.join(mergedFileDirectory, '%s_merged.csv' % (directory_name))

# Save directory paths to each csv file as a list and save in 'all_tables' variable
all_tables = glob.glob(os.path.join(csvDirectory, '*.csv'))

# Create a dataframe of each csv file in the 'all-tables' list
dataframes = [pd.read_csv(table, sep=',') for table in all_tables]

# For each dataframe, set the indexes (or the common columns across the dataframes to join on)
for dataframe in dataframes:
	dataframe.set_index(['dataset_id', 'persistentUrl'], inplace=True)

# Merge all dataframes and save to the 'merged' variable
merged = reduce(lambda left, right: left.join(right, how='outer'), dataframes)

# Export merged dataframe to a csv file
merged.to_csv(filename)
