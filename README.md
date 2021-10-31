# dataverse-scripts

Scripts for automating things in a Dataverse repository/installation, plus some other scripts. The scripts are written using Python 3 and a Mac OS. Compatability with Python 2 and Windows is limited, although I plan to improve compatibility with Windows over time. 

### get_dataset_PIDs.py
Gets the persistent identifiers of any datasets in a given Dataverse installation or a given Dataverse collection within that installation (and optionally all of the Dataverse collections within that Dataverse collection)

### These scripts do things with a given list of dataset PIDs or Dataverse collection IDs or aliases:

| Script or directory                          | Purpose                                                                                                                                                        |
|----------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| change_citation_dates.py                     | Change citation year shown in Dataverse repository's suggested citation for given datasets                                                                     |
| get_dataset_lock_info.py                     | Get information about the locks on given datasets                                                                                                              |
| delete_dataset_locks.py                      | Delete all locks on given datasets                                                                                                                             |
| delete_dataverses.py                         | Delete given Dataverse collections                                                                                                                             |
| destroy_datasets.py                          | Delete given published datasets                                                                                                                                |
| Get and convert metadata of datasets         | A collection of scripts for getting JSON metadata of given datasets and parsing metadata into csv files for metadata analysis, reporting and improving.        |
| move_datasets.py                             | Move given datasets from one Dataverse collection into another                                                                                                 |
| publish_multiple_datasets.py                 | Published given draft datasets (or draft dataset versions)                                                                                                     |
| remove_dataset_links.py                      | Remove given dataset links from a given Dataverse collection                                                                                                   |
| replace_dataset_metadata.py                  | Replace the metadata of given datasets                                                                                                                         |
| curation_report.py                           | This script creates an overview of datasets created in a Dataverse installation in a given time frame, which can be useful for regular dataset curation.       |
| get_dataset_metadata_of_all_installations.py | This script downloads dataset metadata of as many known Dataverse installations as possible. Used to create the dataset at https://doi.org/10.7910/DVN/DCDKZQ. |

### Misc
- **combine_tables.py**: Joins CSV files in a given directory.
- **split_table.py**: Splits a given CSV file into many CSV files based on the unique values in a given column.
  
## Installation
 * Install Python 3, pip and pipenv if you don't already have them. There's a handy guide at https://docs.python-guide.org.
 
 * [Download a zip folder with the files in this GitHub repository](https://github.com/jggautier/dataverse_scripts/archive/refs/heads/main.zip) or clone this GitHub repository:

```
git clone https://github.com/jggautier/get-dataverse-metadata.git
```

 * cd into the dataverse_scripts directory and install packages from [requirements.txt](https://github.com/jggautier/dataverse_scripts/blob/main/requirements.txt)
 ```
pip install -r requirements.txt
```

* Use pipenv when running the scripts so that the packages installed from requirements.txt are available when running any of the scripts (such as `pipenv python change_citation_dates.py`). You can also use `pipenv shell` once so that all following commands in the terminal have access to the packages installed from requirements.txt.
