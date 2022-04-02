# Dataverse repository curation app
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)


A small application for automating things in Dataverse repositories/installations, including:
- Getting dataset metadata as CSV files
- Deleting published datasets (only available to "super user" accounts, usually used by administrators of Dataverse installations)

I plan to add more tasks over time, including:
- Merging dataverse accounts
- Getting the guestbooks of all Dataverse Collections within a dataverse Collection
- Deleting Dataverse Collections (and optionally all collections and datasets within it)
- Changing datasets' citation dates
- Deleting dataset locks
- Getting information about locked datasets in a Dataverse repository
- Moving datasets to different Dataverse Collections
- Publishing datasets
- Removing dataset links in Dataverse Collections

The application is written using the Dataverse software's APIs, Python 3, and Python's tkinter package (for creating the user interface), and made into an executable file using pyInstaller. For now the executable file works only on MacOS and may only work on macOS Monterey (12) and later MacOS versions. I'll be prioritizing work on versions that work on MacOS but eventually I'll try to include a version for Windows.

If you'd like to run the application on earlier versions of MacOS or on other operating systems, or if you run into problems with the exectable file, run the curation_app_main.py file.
