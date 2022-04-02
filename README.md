# dataverse-scripts

This draft branch will contain one or more applications for automating things in Dataverse repositories/installations. The application or applications are being written using the Dataverse software's APIs, Python 3, and Python's tkinter package (for creating the user interface) and will run on MacOS. I'll be prioritizing work on versions that work on MacOS but eventually I'll try to include a version for Windows. 

The application will let people get lists of dataset PIDs and Dataverse Collection aliases and do things with those identifiers. Some of these things require using a repository account that has the right permissions (e.g. getting metadata of unpublished datasets or deleting dataset locks):

- getting the dataset metadata as CSV files
- deleting published datasets
- merging Dataverse accounts
- getting the guestbooks of all Dataverse Collections within a Dataverse Collection
- deleting Dataverse Collections (and optionally all collections and datasets within it)
- changing datasets' citation dates
- deleting dataset locks
- getting information about locked datasets in a Dataverse repository
- moving datasets to different Dataverse Collections
- publishing datasets
- removing dataset links in Dataverse Collections
