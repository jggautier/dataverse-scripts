import pandas as pd
import os

# Directory of the file to split and where the exported csv files should go
os.chdir('path_to_directory')

# Read in csv file
data = pd.read_csv('name_of_file.csv')

# Save the distinct values of the column you want to use to group the data and resave them as a list
nameOfColumn = data['nameOfColumn'].unique()
nameOfColumn = nameOfColumn.tolist()

# Loop through the list of distinct values in the groupby column to create new groups of tables
# and export each as csv files that take the name of the distinct value
for i, value in enumerate(nameOfColumn):
    data[data['nameOfColumn'] == value].to_csv(str(value) + r'.csv', index=False)
