# Dataverse repository curation assistant
A small software application for automating things in repositories that use the Dataverse software (https://dataverse.org). With this application you can:
- Get dataset metadata as CSV files
  - If you need all dataset metadata from any known Dataverse reposiories, instead of using this app please consider downloading the metadata already collected and published in the dataset at https://doi.org/10.7910/DVN/8FEGUV
- Delete published datasets
  - This requires the API token of a "super user" account, usually used by administrators of Dataverse installations
- Get information about locked datasets and remove dataset locks
  - This requires the API token of a "super user" account, usually used by administrators of Dataverse installations

<img width="964" alt="screenshot" src="https://user-images.githubusercontent.com/18374574/177402806-48d258bc-9fb0-4f8b-a8a2-e48a2d00f307.png">

You can import your credentials from a Dataverse repository by clicking the "Import credentials" button and choosing a YAML file from your computer. The Installation URL and API Token fields will be filled with the URL and token from the selected YAML file. You can download [the sample YAML file](https://github.com/jggautier/dataverse-scripts/blob/main/dataverse_repository_curation_assistant/credentials.yaml) and add your credentials.

The application is written using the [Dataverse software's APIs](https://guides.dataverse.org/en/5.10/api/index.html), Python 3, and Python's [tkinter library](https://docs.python.org/3/library/tkinter.html) (for creating the graphical user interface), and made into an executable file using [pyInstaller](https://pyinstaller.readthedocs.io/).

## Status
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

## Opening the software application...
### By downloading and clicking on an application file
The file works only on MacOS and may work only on macOS Monterey (12) and later MacOS versions. To use it:
* [Visit the releases page](https://github.com/jggautier/dataverse-scripts/releases) to download the latest version of the ZIP file (Dataverse.repository.curation.assistant.zip). If you're using Google Chrome when you download the ZIP file, keep an eye out for the browser warning you about downloading the ZIP file. You might have to tell Google Chrome that the download is safe
* Extract the ZIP file's "Dataverse repository curation assistant" file
* Right click on the application file and choose Open. MacOS may display a warning that “Dataverse repository curation assistant” can’t be opened because Apple cannot check it for malicious software. This is because the application is not in Apple's App Store. (See [Apple's support article](https://support.apple.com/guide/mac-help/apple-cant-check-app-for-malicious-software-mchleab3a043/mac) for more info about this warning.)
* Click "Open" and wait for the application to appear
* The application will be saved as an exception to your computer's security settings, and you'll be able to open it again by double-clicking it as you would other Desktop applications

If you re-download the application file from this GitHub repo, e.g. to use a future version with more functionality or bug fixes, you'll have to follow these steps again to re-add the application as an exemption to your computer's security settings.

### By downloading and running a Python script
If you'd like to run the application on earlier versions of MacOS or if you run into problems with the application file, you can run the dataverse_repository_curation_app_main.py file, which will create the application's UI. You'll need Python 3 installed and may need Python 3.7 or later, as well as the Python libraries listed in the [requirements.txt file](https://github.com/jggautier/dataverse-scripts/blob/main/dataverse_repository_curation_assistant/requirements.txt) and some familiarity with running Python scripts:

* Install Python 3, pip and pipenv if you don't already have them. There's a handy guide at https://docs.python-guide.org.
 
 * [Download a zip folder with the files in this GitHub repository](https://github.com/jggautier/dataverse-scripts/archive/refs/heads/main.zip) or clone this GitHub repository:

```
git clone https://github.com/jggautier/dataverse-scripts.git
```

 * In your terminal, cd into the dataverse_repository_curation_app directory and use `pipenv shell` so that library dependencies for these scripts are managed separately from any Python libraries already on your system
 * Install packages from the requirements.txt file
```
pip install -r requirements.txt
```
 * Run dataverse_repository_curation_assistant_main.py to run the application

Note: The tkinter library comes with most installations of Python 3, so pip doesn't include it in the requirements.txt it produces. But if after installing libraries in a pipenv shell, you get error messages about tkinter not being defined, you may have to install tkinter "manually". For example, if you use homebrew's version of Python 3, you might have to `brew install python-tk`