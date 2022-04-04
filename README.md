# Dataverse repository curation app
A small software application for automating things in repositories that use the Dataverse software (https://dataverse.org). With this application you can:
- Get dataset metadata as CSV files
- Delete published datasets (to do this you'll need a "super user" account, usually used by administrators of Dataverse installations)

The application is written using the Dataverse software's APIs, Python 3, and Python's tkinter library (for creating the user interface), and made into an executable file using [pyInstaller](https://pyinstaller.readthedocs.io/).

## Status
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)  
Work in progress: Usability testing, fixing UI bugs, adding more documentation 

## Opening the software application...
### By downloading and clicking on a file
The file works only on MacOS and may work only on macOS Monterey (12) and later MacOS versions. To use it:
* [Download the ZIP file](https://github.com/jggautier/dataverse-scripts/raw/main/Dataverse%20Repository%20Curation%20App.zip). If you're using Google Chrome, keep an eye out for the browser giving a warning about downloading the ZIP file. You might have to tell Google Chrome that the download is safe
* Extract the Zip file's Dataverse Repository Curation App file
* Right click on the file and choose Open. MacOS may display a warning that “Dataverse Repository Curation App” can’t be opened because Apple cannot check it for malicious software. This is because the application is not in Apple's App Store. (See [Apple's support article](https://support.apple.com/guide/mac-help/apple-cant-check-app-for-malicious-software-mchleab3a043/mac) for more info about this warning.)
* Click "Open" and wait for the application to appear
* The file will be saved as an exception to your computer's security settings, and you'll be able to open it again by double-clicking it as you would any other file

If you re-download the file from this GitHub repo, e.g. to use a future version with more functionality or bug fixes, you'll have to follow these steps again to re-add the application as an exemption to your computer's security settings.

### By using a Python script
If you'd like to run the application on earlier versions of MacOS or on other operating systems, or if you run into problems with the exectable file, you can run the curation_app_main.py file. You'll need Python 3 installed and may need Python 3.7 or later, as well as the Python libraries listed in the [requirements.txt file](https://github.com/jggautier/dataverse-scripts/blob/main/dataverse_repository_curation_app/requirements.txt):

* Install Python 3, pip and pipenv if you don't already have them. There's a handy guide at https://docs.python-guide.org.
 
 * [Download a zip folder with the files in this GitHub repository](https://github.com/jggautier/dataverse-scripts/archive/refs/heads/main.zip) or clone this GitHub repository:

```
git clone https://github.com/jggautier/dataverse-scripts.git
```

 * Iin your terminal, cd into the dataverse_repository_curation_app directory and use `pipenv shell` so that package dependencies for these scripts are managed separately from any Python packages already on your system
 * Install packages from the requirements.txt file
```
pip install -r requirements.txt
```
 * Run dataverse_repository_curation_app_main.py to run the application

Note: The tkinter library comes with most installations of Python 3, so pip doesn't include it in the requirements.txt it produces. But if after installing packages in a pipenv shell, you get error messages about tkinter not being defined, you may have to install tkinter "manually". For example, if you use homebrew's version of Python 3, you might have to `brew install python-tk`

## Upcoming changes

I plan to add more functionality to the application over time, including:
- Merging user accounts in a Dataverse repository
- Getting information about locked datasets in a Dataverse repository
- Deleting dataset locks
- Getting the guestbooks of all Dataverse Collections within a Dataverse Collection
- Deleting Dataverse Collections (and optionally all collections and datasets within it)
- Changing datasets' citation dates
- Moving datasets to different Dataverse Collections
- Publishing datasets
- Removing dataset links in Dataverse Collections

## Other scripts
The [other_scripts directory](https://github.com/jggautier/dataverse-scripts/tree/main/other_scripts) contains Python scripts I've written over the past three years for automating some common curation and research-related tasks. Some of these scripts do what the Dataverse repository curation app does or will do. I'll remove these scripts from the directory as the scripts functionality gets added to the application.
