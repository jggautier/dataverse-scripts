# dataverse-scripts
Scripts for automating things in a Dataverse repository/installation, plus some other scripts. The scripts are written using Python 3 and a Mac OS. Compatability with Python 2 and Windows is limited, although I plan to improve compatibility with Windows over time. 

### get_dataset_PIDs.py
Gets the persistent identifiers of any datasets in a given Dataverse installation or a given dataverse within that installation (and optionally all of the dataverses within that dataverse)

### These scripts do things with a given list of dataset PIDs:

- #### change_citation_dates.py
- #### destroy-datasets.py
- #### [get-dataverse-metadata](https://github.com/jggautier/dataverse-scripts/tree/master/get-dataverse-metadata):
  A collection of scripts for getting JSON metadata of given datasets and parsing metadata into csv files for metadata analysis, reporting and improving.
- #### link_datasets.py
- #### unlock_datasets.py

### curation-report.py
This script creates an overview of datasets created in a Dataverse-based installation in a given time frame, which can be useful for regular curation.

### get_dataset_metadata_of_all_installations.py
This script downloads dataset metadata of as many known Dataverse-based installations as possible. Used to create the dataset at https://doi.org/10.7910/DVN/DCDKZQ.

### Misc
- #### publish_multiple_datasets.command
  This script publishes the unpublished datasets or draft versions in a given dataverse.
- #### replace_dataset_metadata_in_a_dataverse.command
  This script replaces the metadata of datasets in a given dataverse with the metadata in a given JSON file.
- #### destroy_all_datasets_in_a_dataverse.command
  This script destroys all datasets in a given dataverse.
- #### split_table.py
  This script splits a given CSV file into many csv files based on the unique values in a given column. It's like the opposite of a JOIN.
- #### combine_tables.py
  This script does a join on CSV files in a given directory.
