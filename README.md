# dataverse-scripts

Scripts for automating things in a Dataverse repository/installation, plus some other scripts. The scripts are written using Python 3, pipenv to manage package dependencies, and a Mac OS. You might have limted success using these scripts in a Windows OS.

Some of these scripts use the Python package [tkinter](https://docs.python.org/3/library/tkinter.html) to create a form UI that is used to collect information, such as the URL of a Dataverse installation or the location of a CSV file listing dataset PIDs, before the script is run. tkinter comes with most installations of Python 3, so pip doesn't include it in the requirements.txt it produces. But if after installing packages in a pipenv shell, you get error messages about tkinter not being defined, you may have to install tkinter "manually". For example, if you use homebrew's version of Python 3, you might have to `brew install python-tk`.

### get_dataset_PIDs.py
Gets the persistent identifiers and some other basic information of datasets in a given Dataverse installation or a given Dataverse Collection within that installation (and optionally all of the Dataverse Collections within that Dataverse Collection)

### These scripts do things with a given list of either dataset PIDs or of Dataverse Collection IDs/aliases:

| Script or directory                          | Purpose                                                                                                                                                        |
|----------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| change_citation_dates.py                     | Change citation year shown in Dataverse repository's suggested citation                                            |
| get_dataset_lock_info.py                     | Get information about locks on given datasets                                                                                                              |
| delete_dataset_locks.py                      | Delete all locks of given datasets                                                                                                                             |
| delete_dataverses.py                         | Delete given Dataverse Collections                                                                                                                             |
| destroy_datasets.py                          | Delete given published datasets                                                                                                                                |
| [Get and convert metadata of datasets](https://github.com/jggautier/dataverse-scripts/tree/main/get-dataverse-metadata)         | A collection of scripts for getting JSON metadata of given datasets and parsing metadata into CSV files for metadata analysis, reporting and improving.        |
| move_datasets.py                             | Move given datasets from one Dataverse Collection into another Dataverse Collection                                                                                                 |
| publish_multiple_datasets.py                 | Publish given draft datasets (or draft dataset versions)                                                                                                     |
| remove_dataset_links.py                      | Remove given dataset links from a given Dataverse Collection                                                                                                   |
| replace_dataset_metadata.py                  | Replace the metadata of given datasets                                                                                                                         |

### Misc
- **get_dataset_metadata_of_all_installations.py**: This script downloads dataset metadata of as many known Dataverse installations as possible. Used to create the dataset at https://doi.org/10.7910/DVN/DCDKZQ.
- **join_csv_files.py**: This script performs [outer joins](https://dataschool.com/how-to-teach-people-sql/full-outer-join-animated/) on two or more CSV files. Useful for joining the tables produced by [the "parse..." scripts](https://github.com/jggautier/dataverse-scripts/tree/main/get-dataverse-metadata/parse_metadata_fields).
- **split_csv_files.py**: This script splits a given CSV file into many CSV files based on the unique values in a given column.
- **get_oaipmh_records.py**: This script writes the identifiers and statuses of records in a given OAI-PMH server and set.
  
## Installation
 * Install Python 3, pip and pipenv if you don't already have them. There's a handy guide at https://docs.python-guide.org.
 
 * [Download a zip folder with the files in this GitHub repository](https://github.com/jggautier/dataverse-scripts/archive/refs/heads/main.zip) or clone this GitHub repository:

```
git clone https://github.com/jggautier/dataverse-scripts.git
```

 * cd into the dataverse-scripts directory and use `pipenv shell` so that package dependacies for these scripts are managed separately from any Python packages already on your system
 * Install packages from [requirements.txt](https://github.com/jggautier/dataverse-scripts/blob/main/requirements.txt)
 ```
pip install -r requirements.txt
```
 * Run any of the Python scripts, such as get_dataset_PIDs.py
