# dataverse-automation
Scripts for automating things in a Dataverse repository, plus some other scripts:

### get_dataset_PIDs.py
Gets the persistent identifiers of any datasets in a given dataverse (and optionally any of the given dataverse's subdataverses)

### These scripts do things with a given list of dataset PIDs:

- #### change_citation_dates.py
- #### destroy-datasets.py
- #### destroy_all_datasets_in_a_dataverse.command
- #### [get-dataverse-metadata](https://github.com/jggautier/dataverse-scripts/tree/master/get-dataverse-metadata):
  A collection of scripts for getting JSON metadata of given datasets and parsing metadata into csv files for metadata analysis, reporting and improving.
- #### link_datasets.py
- #### publish_multiple_datasets.command
- #### replace_dataset_metadata_in_a_dataverse.command
- #### unlock_datasets.py

### curation-report.py
This script creates an overview of datasets created in a Dataverse-based repository in a given time frame, which can be useful for regular repository curation.

### download_all_files_in_a_dataset.sh
This broken script used to download all files in given dataset. 

### Misc
- #### split_table.py
  This script splits a given csv file into many csv files based on the unique values in a given column. It's like the opposite of a JOIN.
- #### combine_tables.py
