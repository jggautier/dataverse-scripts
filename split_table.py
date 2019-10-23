import pandas as pd
import os

# Directory of the file to split and where the exported csv files should go
os.chdir('/Users/juliangautier/Desktop')

# Read in csv file
data = pd.read_csv('name_of_file.csv')

# Save the distinct values of the column you want to use to group the data
name_of_column = data['name_of_column'].unique()
name_of_column = name_of_column.tolist()

# Loop through the distinct values in the groupby column to create new groups of tables 
# and export each as csv files that take the name of the distinct value
for i,value in enumerate(name_of_column):
    data[data['name_of_column'] == value].to_csv(str(value)+r'.csv',index = False)