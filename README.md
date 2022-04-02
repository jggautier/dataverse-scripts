# Dataverse repository curation app
A small application for automating things in Dataverse repositories/installations, including:
- Getting dataset metadata as CSV files
- Deleting published datasets (only available to "super user" accounts, usually used by administrators of Dataverse installations)

The application is written using the Dataverse software's APIs, Python 3, and Python's tkinter package (for creating the user interface), and made into an executable file using pyInstaller.

## Status
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)  
Work in progress: Doing usability testing, fixing UI bugs, adding more documentation 

## Using the application
### Executable file
The executable file works only on MacOS and may only work on macOS Monterey (12) and later MacOS versions. To use it, [download the ZIP file](https://github.com/jggautier/dataverse-scripts/raw/main/Dataverse%20Repository%20Curation%20App.zip), and extract the Dataverse Repository Curation App file.

### Python script
If you'd like to run the application on earlier versions of MacOS or on other operating systems, or if you run into problems with the exectable file, you can run the curation_app_main.py file. You'll need Python 3 installed and may need Python 3.7 or later, as well as the Python libraries listed in the [requirements.txt file](https://github.com/jggautier/dataverse-scripts/blob/main/dataverse_repository_curation_app/requirements.txt).

## Upcoming changes

I plan to add more functionality to the application over time, including:
- Merging dataverse accounts
- Getting the guestbooks of all Dataverse Collections within a dataverse Collection
- Deleting Dataverse Collections (and optionally all collections and datasets within it)
- Changing datasets' citation dates
- Deleting dataset locks
- Getting information about locked datasets in a Dataverse repository
- Moving datasets to different Dataverse Collections
- Publishing datasets
- Removing dataset links in Dataverse Collections

## Other scripts
The [other_scripts directory](https://github.com/jggautier/dataverse-scripts/tree/main/other_scripts) contains Python scripts I've written over the past three years for automating some common curation and research-related tasks. Some of these scripts do what the Dataverse repository curation app does or will do. I'll remove these scripts from the directory as the scripts functionality gets added to the application.
