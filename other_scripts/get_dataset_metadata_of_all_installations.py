# Download dataset metadata of as many known Dataverse installations as possible

from bs4 import BeautifulSoup
import contextlib
import csv
from csv import DictReader
import joblib
from joblib import Parallel, delayed
import json
import os
from pathlib import Path
import pandas as pd
import requests
import sys
import time
from tqdm import tqdm
from urllib.parse import urlparse


def get_dataverse_functions():
    # Saves a Python file containing functions for doing things with Dataverse repositories
    # and returns the path of the folder that contains the file so the functions can be loaded
    # and the folder can be deleted at the end of the script

    # Get latest Python file from my GitHub 
    response = requests.get(
      url='https://raw.githubusercontent.com/jggautier/dataverse-scripts/main/dataverse_repository_curation_assistant/dataverse_repository_curation_assistant_functions.py')

    # Create folder and file paths
    functionsDirectoryPath = f'{os.getcwd()}/dataversescriptfunctions'
    dataverseFunctionsFileDirectoryPath = f'{functionsDirectoryPath}/dataversescriptfunctions.py'

    # Create folder
    os.mkdir(functionsDirectoryPath)

    # Save Python file
    with open(dataverseFunctionsFileDirectoryPath, mode='wb') as file:
        file.write(response.content)

    return functionsDirectoryPath


functionsDirectoryPath = get_dataverse_functions()
sys.path.append(functionsDirectoryPath)
from dataversescriptfunctions import *


userAgent = ''
emailAddress = ''

headers = {
    'User-Agent': userAgent,
    'From': emailAddress}

installationHostnamesList = [
    ]

get_dataverse_installations_metadata(
    mainInstallationsDirectoryPath='', 
    apiKeysFilePath='', 
    installationHostnamesList=installationHostnamesList, 
    nJobsForApiCalls=3,
    requestTimeout=60,
    headers=headers)


shutil.rmtree(functionsDirectoryPath)
