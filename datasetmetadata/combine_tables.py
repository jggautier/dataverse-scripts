# Join (full outer join) csv files in a given directory

import os
import glob
import pandas as pd
from tkinter import filedialog
from tkinter import *
from functools import reduce

# Ask user to choose folder that contains csv files
root = Tk()
root.withdraw()
# root.update()
tables_directory = filedialog.askdirectory()
directory_name = tables_directory.split('/')[-1]

# Create csv file in directory where script lives
current_directory = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(current_directory,'%s_merged.csv' %(directory_name))

# Save directory paths to each csv file as a list and save in 'all_tables' variable
all_tables = glob.glob(os.path.join(tables_directory,'*.csv'))

# Create a dataframe of each csv file in the 'all-tables' list
dataframes = [pd.read_csv(table, sep = ',') for table in all_tables]

# For each dataframe, set the indexes (or the common columns across the dataframes to join on)
for dataframe in dataframes:
	dataframe.set_index(['dataset_id', 'persistentUrl'], inplace = True)

# Merge all dataframes and save to the 'merged' variable
merged = reduce(lambda left, right: left.join(right, how = 'outer'), dataframes)

# Export merged dataframe to a csv file
merged.to_csv(filename)
