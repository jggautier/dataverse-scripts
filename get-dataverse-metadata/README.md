# Get and convert metadata of datasets
This is a collection of Python 3 scripts for getting the metadata of published datasets in a [Dataverse](https://dataverse.org/)-based repository, in the Dataverse JSON format, and writing the metadata to CSV files for analysis, reporting, and metadata improvement.

The metadata of datasets published in the [Harvard Dataverse repository](https://dataverse.harvard.edu) are published in Harvard Dataverse: https://doi.org/10.7910/DVN/DCDKZQ. The metadata is current as of December 12, 2019. Consider downloading the JSON metadata from there instead of using the scripts to re-download the JSON files from Harvard Dataverse.

## General
The scripts can be grouped into three types of scripts:
 * One script, get_dataset_json_metadata.py, takes a list of dataset PIDs and downloads the metadata of the latest published versions of those datasets (in the Dataverse JSON standard)
 * Several scripts, such as get_basic_metadata.py, get_authors.py and get_relatedpublications.py, parse the JSON files to extract metadata fields in Dataverse's Citation metadata block and write them into CSV files
 * One script, combine_tables.py, joins a given collection of CSV files into one CSV file

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

The script will retrieve metadata of only dataset PIDs that have been published in the given Dataverse-based repository. It will ignore PIDs of unpublished datasets and datasets that have been deaccessioned.

If you're using Mac OS, you may see a message in your terminal that starts with "Class FIFinderSyncExtensionHost", which can be ignored. ([See the FAQ](https://github.com/jggautier/get-dataverse-metadata/tree/tkinter-gui#faq) for more info.)

In the window that pops up, enter the URL of the Dataverse-based repository whose datasets you're interested in, browse to the folder you want to store the JSON files in, and click Start.

Within the directory that you specified, the script will create a folder to store the downloaded JSON metadata files.

For each published dataset in the specified dataverse, the script will save a JSON file containing the metadata of the latest published dataset version.

### Writing metadata from JSON files to CSV files
Run any of the scripts that start with get_, such as get_basic_metadata.py

```
python3 get_basic_metadata.py
```

In the window that pops up, browse to the folder that contains the JSON files with the metadata you want, browse to the folder you want to store the CSV files in, and click Start.

 * Running get_basic_metadata.py will create a CSV file where the values of basic metadata fields are written, such as dataset_id, publication date, and version number.
 * Running get_primitive_fields.py will create multiple CSV files, one for each of the fields in Dataverse's Citation metadata block that do not contain subfields, called "primitive fields," such as title, subtitle, subject and production date.
 * Running any one of the scripts whose names contain the names of metadata fields will create a CSV file for each script. These scripts get the metadata of compound fields. For example, running get_relatedpublication.py will create a CSV file containing the values of the related publication fields contained in the given JSON files.

### Combining CSV files
You might want to join two or more tables to see which datasets have and don't have certain metadata values. Run the combine_tables.py script to join two or more tables.

```
python3 combine_tables.py
```

In the window that pops up, browse to the folder that contains the CSV files you want to combine, browse to the folder you want to store the resulting CSV file in, and click Start.

 * The script does a full outer join on the dataset_id and persistentUrl columns present in every CSV file.

## Further reading
For more information about Dataverse's metadata model, see the [Appendix of Dataverse's User Guide](http://guides.dataverse.org/en/latest/user/appendix.html) 

## FAQ
 * The scripts that create the CSV files look for fields in Dataverse's standard Citation metadata block. They can be adjusted, particularly the get_primitive_fields.py script, to get metadata in other metadata blocks.
 * More scripts can be added to get the values of additional compound metadata fields.
 * Python 2 is not supported primarily because I couldn't get Python 2's version of the CSV module to encode the JSON values as utf-8 before writing metadata values to CSV files. So I switched to Python 3 (and never looked back).
 * The "get_dataset_json_metadata.py" script won't work if the Dataverse repository requires an API key in order to use a Native API endpoint to download dataset metadata.
 * For Mac OS users, some scripts return a message that starts with "objc[1775]: Class FIFinderSyncExtensionHost". It's related to the use of a module called tkinter, which creates a UI to accept user input. The message should not stop the scripts from working. More information about a similar message is at https://stackoverflow.com/questions/46999695/class-fifindersyncextensionhost-is-implemented-in-both-warning-in-xcode-si, in which some people agree that it's a MacOS problem that can be ignored.
