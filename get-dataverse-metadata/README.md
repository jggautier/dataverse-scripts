# Get and convert metadata of datasets
This is a collection of Python 3 scripts for getting the metadata of published datasets in a [Dataverse](https://dataverse.org/)-based repository, in the Dataverse JSON format, and writing the metadata to CSV files for analysis, reporting, and metadata improvement.

If you're interested in getting the metadata of all datasets in most known Dataverse-based repositories, the metadata is already published in a dataset in the Harvard Dataverse repository: https://doi.org/10.7910/DVN/DCDKZQ.

## General
The scripts can be grouped into three types of scripts:
 * One script, get_dataset_json_metadata.py, takes a list of dataset PIDs and downloads the metadata of either the latest published version or all published versions of those datasets (in the Dataverse JSON standard). If a Dataverse account API key is included, the script will download draft and deaccessioned versions of any datasets accessible by the Dataverse account.
 * Several scripts, such as parse_basic_metadata.py and parse_metadatablock_metadata.py, parse the JSON files to extract metadata fields and write that metadata into CSV files.

You can manipulate and analyze the metadata in the CSV files using many methods and tools, including MS Excel, Apple's Numbers, Google Sheets, OpenRefine, R, Python, and database applications like pgAdmin or DB Browser for SQLite.

## Installation
 * Install Python 3 if you don't already have it. There's a handy guide at https://docs.python-guide.org.
 
 * [Download a zip folder with the files in this repository](https://github.com/jggautier/get-dataverse-metadata/archive/master.zip) or clone this repository:

```
git clone https://github.com/jggautier/get-dataverse-metadata.git
```

 * Install the Python modules [pandas](https://pandas.pydata.org/about.html) and [pyDataverse](https://pydataverse.readthedocs.io/en/latest/index.html):
```
pip3 install pandas pyDataverse
```

## Using the scripts
Imagine you want to get and analyze the metadata of datasets in a Dataverse-based repository, such as [demo.dataverse.org](https://demo.dataverse.org/), or in a dataverse in that repository, for any number of reasons, including:
 * Improving the metadata of datasets in your dataverse
 * Reporting to research funders the quality of metadata in your dataverse
 * Studying and reporting data is described to recommend better ways of describing and using data

### Getting dataset PIDs
To get a CSV file with information about datasets in a dataverse, including their persistent identifiers, run [get_dataset_pids.py](https://github.com/jggautier/dataverse-scripts/blob/master/get_dataset_PIDs.py) in your terminal.

### Getting dataset metadata
Run get_dataset_json_metadata.py, which asks for a list of dataset PIDs (either a txt file or a CSV file where one column has the PIDs).

```
python3 get_dataset_json_metadata.py
```

The script creates a UI where you must enter the URL of the dataverse repository, enter an optional API key, indicate if you want the metadata of all dataset versions or just the latest version, and indicate the location of the CSV or text file containing the dataset PIDs you're interested in and where you want to save the metadata files and metadatablock JSON files of the repository. If you're using Mac OS, when you press "Start" in the UI, you may see a message in your terminal that starts with "Class FIFinderSyncExtensionHost", which can be ignored. ([See the FAQ](https://github.com/jggautier/get-dataverse-metadata/tree/tkinter-gui#faq) for more info.)

Within the directory that you specified, the script will create a folder, whose name will include a timestamp, to store the downloaded JSON metadata files.

For each dataset PID in the provided text file, the script will save a JSON file containing the metadata of the latest version of each dataset (unless you indicated that you'd like the metadata of each dataset version). If a Dataverse account API key is included, the script will also download the draft and deaccessioned versions of any datasets accessible by the Dataverse account.

### Writing metadata from JSON files to CSV files
Run any of the scripts that start with parse_, such as parse_basic_metadata.py

```
python3 parse_basic_metadata.py
```

Each script will generate a UI that asks for certain files and directories on your computer, depending on the script.

 * Running parse_basic_metadata.py will create a CSV file where the values of basic metadata fields, that aren't part of any metadatablocks, are written, such as the repository's database ID for the dataset version, the dataset's creation time, its publication date, and any major and minor version numbers.
 * Running parse_terms_metadata.py will create a CSV file where the values of the Terms of Use and Access metadata fields are written, such as Waiver, Terms of Use, and Terms of Access.
 * Running parse_metadatablock_metadata.py will create multiple CSV files, one for each field in a given metadatablock JSON file. You'll be asked for a metadatablock JSON file that contains information about the fields you're interested in parsing into CSV files. (The get_dataset_json_metadata.py script also retrieves the Dataverse installation's metadatablock JSON files. Or you can use the Native API endpoints documented at http://guides.dataverse.org/en/latest/api/native-api.html#metadata-blocks to get the JSON files of metadatablocks whose fields you're interested in.)

### Analyzing using the CSV files
To analyze the metadata, you can manipulate and analyze them using many methods, including MS Excel, Apple's Numbers, Google Sheets, OpenRefine, R, Python, and database applications like pgAdmin or DB Browser for SQLite. The combine_tables.py script is provided to quickly join all of the CSV files in a directory full of CSV files, joining on the datasetVersionId and persistentUrl columns.

## Further reading
For more information about the metadata model that ships with the Dataverse software, including the database names of each field, see the [Appendix of Dataverse's User Guide](http://guides.dataverse.org/en/latest/user/appendix.html). Harvard Dataverse's metadata model is the same model that ships with the Dataverse software, but each Dataverse-based repository is able to change this model (for example, they may have different fields and different parent/child relationships between fields).

## FAQ
 * The "get_dataset_json_metadata.py" script won't work if the Dataverse repository requires an API key in order to use a few Dataverse Native API endpoints to download dataset metadata, such as the Search API endpoints. If the script throws an error, this might be the reason.
 * For Mac OS users, some scripts return a message that starts with "objc[1775]: Class FIFinderSyncExtensionHost". It's related to the use of a module called tkinter, which I use to create a UI to accept user input. The message should not stop the scripts from working. More information about a similar message is at the thread at https://stackoverflow.com/questions/46999695/class-fifindersyncextensionhost-is-implemented-in-both-warning-in-xcode-si, in which some people agree that it's a MacOS problem that can be safely ignored.
