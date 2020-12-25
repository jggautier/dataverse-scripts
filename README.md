# dataverse-scripts

Scripts for automating things in a Dataverse repository/installation, plus some other scripts. The scripts are written using Python 3 and a Mac OS. Compatability with Python 2 and Windows is limited, although I plan to improve compatibility with Windows over time. 

### get_dataset_PIDs.py
Gets the persistent identifiers of any datasets in a given Dataverse installation or a given Dataverse collection within that installation (and optionally all of the Dataverse collections within that Dataverse collection)

### These scripts do things with a given list of dataset PIDs or Dataverse collection IDs or aliases:

- #### change_citation_dates.py
- #### delete_dataset_locks.py
- #### delete_dataverses.py
- #### destroy_datasets.py
- #### [Get and convert metadata of datasets](https://github.com/jggautier/dataverse-scripts/tree/master/get-dataverse-metadata):
  A collection of scripts for getting JSON metadata of given datasets and parsing metadata into csv files for metadata analysis, reporting and improving.
- #### publish_multiple_datasets.py
- #### replace_dataset_metadata.py

### curation_report.py
This script creates an overview of datasets created in a Dataverse installation in a given time frame, which can be useful for regular dataset curation.

### get_dataset_metadata_of_all_installations.py
This script downloads dataset metadata of as many known Dataverse installations as possible. Used to create the dataset at https://doi.org/10.7910/DVN/DCDKZQ.

### Misc
- #### combine_tables.py
  This script does a join on CSV files in a given directory.
- #### split_table.py
  This script splits a given CSV file into many csv files based on the unique values in a given column. It's like the opposite of a JOIN.
