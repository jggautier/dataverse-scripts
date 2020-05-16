# Get and convert metadata of datasets
This is a collection of Python 3 scripts for getting the metadata of published datasets in a [Dataverse](https://dataverse.org/)-based repository, in the Dataverse JSON format, and writing the metadata to CSV files for analysis, reporting, and metadata improvement.

If you're interested in getting the metadata of all datasets in the [Harvard Dataverse repository](https://dataverse.harvard.edu), the metadata is already published in dataset in the Harvard Dataverse repository: https://doi.org/10.7910/DVN/DCDKZQ. The metadata is current as of December 12, 2019.

## General
The scripts can be grouped into three types of scripts:
 * One script, get_dataset_json_metadata.py, takes a list of dataset PIDs and downloads the metadata of the latest published versions of those datasets (in the Dataverse JSON standard)
 * Several scripts, such as parse_basic_metadata.py and parse_compound_metadata.py, parse the JSON files to extract metadata fields in Dataverse's Citation metadata block and write them into CSV files

To analyze the metadata, you can add the csv files to a database app, e.g. pgAdmin or DB Browser for SQLite, or join them using combine_tables.py or any of the many methods for joining tables.

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
 * Studying and reporting how certain types of data are described to recommend better ways of describing data

### Getting dataset PIDs
To get a text file with a list of persistent identifiers of datasets in a dataverse, run [get_dataset_pids.py](https://github.com/jggautier/dataverse-scripts/blob/master/get_dataset_PIDs.py) in your terminal.

### Getting dataset metadata
Run get_dataset_json_metadata.py, which asks for the list of dataset PIDs.

```
python3 get_dataset_json_metadata.py
```

The script creates a UI for entering the URL of the dataverse repository, the location of the text file containing the dataset PIDs you're interested in, and where you want to save the metadata files. If you're using Mac OS, upon pressing "Start" in the UI, you may see a message in your terminal that starts with "Class FIFinderSyncExtensionHost", which can be ignored. ([See the FAQ](https://github.com/jggautier/get-dataverse-metadata/tree/tkinter-gui#faq) for more info.)

Within the directory that you specified, the script will create a folder, whose name will include a timestamp, to store the downloaded JSON metadata files.

For each published dataset in the specified dataverse, the script will save a JSON file containing the metadata of the latest published dataset version.

### Writing metadata from JSON files to CSV files
Run any of the scripts that start with parse_, such as parse_basic_metadata.py

```
python3 parse_basic_metadata.py
```

In the window that pops up, browse to the folder that contains the JSON files with the metadata you want, browse to the folder you want to store the CSV files in, and click Start.

 * Running parse_basic_metadata.py will create a CSV file where the values of basic metadata fields are written, such as dataset_id, publication date, and version number.
 * Running parse_primitive_metadata.py will create multiple CSV files, one for each of the fields in Dataverse's Citation metadata block that do not contain subfields, called "primitive fields," such as title, subtitle, subject and production date.
 * To get the metadata of a parse_compound_field, open parse_compound_fields.py, edit the script to specify the database name of the field, save it and then run it.

### Analyzing using the CSV files
To analyze the metadata, you can add the CSV files to a database app, e.g. pgAdmin or DB Browser for SQLite, or join them using combine_tables.py or any of the many methods for joining tables.

## Further reading
For more information the metadata model that ships with the Dataverse software, including the database names of each field, see the [Appendix of Dataverse's User Guide](http://guides.dataverse.org/en/latest/user/appendix.html). Harvard Dataverse's metadata model is the same model that ships with the Dataverse software, but each Dataverse-based repository is able to change this model (e.g. they may have different fields and hierarchies) and learning about a repository's custom metadata model may take some investigation of the repository.

## FAQ
 * The scripts that create the CSV files look for fields in Dataverse's standard Citation metadata block. They can be adjusted, particularly the parse_primitive_fields.py script, to get metadata in other metadata blocks.
 * Python 2 is not supported primarily because I couldn't get Python 2's version of the CSV module to encode the JSON values as utf-8 before writing metadata values to CSV files. So I switched to Python 3 (and never looked back).
 * The "get_dataset_json_metadata.py" script won't work if the Dataverse repository requires an API key in order to use a Native API endpoint to download dataset metadata. If the script throws an error, this might be the reason.
 * For Mac OS users, some scripts return a message that starts with "objc[1775]: Class FIFinderSyncExtensionHost". It's related to the use of a module called tkinter, which I use to create a UI to accept user input. The message should not stop the scripts from working. More information about a similar message is at the thread at https://stackoverflow.com/questions/46999695/class-fifindersyncextensionhost-is-implemented-in-both-warning-in-xcode-si, in which some people agree that it's a MacOS problem that can be safely ignored.
