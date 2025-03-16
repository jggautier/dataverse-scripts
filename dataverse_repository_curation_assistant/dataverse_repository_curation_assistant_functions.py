from bs4 import BeautifulSoup
import contextlib
import csv
from datetime import datetime
from dateutil import tz
from dateutil.parser import parse
from functools import reduce
from fuzzywuzzy import fuzz, process
import io
import json
import joblib
from joblib import Parallel, delayed
import glob
import math
import os
from os import listdir
import math
from packaging.version import Version
import pandas as pd
from pathlib import Path
import re
import requests
import time
from time import sleep
from tkinter import Tk, ttk, Frame, Label, IntVar, Checkbutton, filedialog, NORMAL, DISABLED
from tkinter import Listbox, MULTIPLE, StringVar, END, INSERT, N, E, S, W
from tkinter.ttk import Entry, Progressbar, OptionMenu, Combobox
from tqdm import tqdm
tqdm_bar_format = "{l_bar}{bar:10}{r_bar}{bar:-10b}"
from urllib.parse import urlparse
import xmltodict
import yaml

from requests.packages.urllib3.exceptions import InsecureRequestWarning
# The requests module isn't able to verify the SSL cert of some Dataverse installations,
# so when requests calls in this script that are set to not verify certs (verify=False),
# which suppresses the warning messages that are thrown when requests are made without verifying SSL certs
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Class for custom collapsiblePanel frame using tkinter widgets
class collapsiblePanel(Frame):

    def __init__(self, parent, text='', default='closed', padx=0, pady=0, *args, **options):
        Frame.__init__(self, parent, *args, **options, padx=padx, pady=pady)

        self.show = IntVar()

        self.titleFrame = ttk.Frame(self, relief='raised', borderwidth=1)
        self.titleFrame.pack(fill='x', expand=1)

        Label(self.titleFrame, text=text, width=40, anchor='w').pack(side='left', fill='x', expand=1)

        self.toggleButton = ttk.Checkbutton(
            self.titleFrame, width=5, command=self.toggle,
            variable=self.show, style='Toolbutton')
        self.toggleButton.pack(side='right')

        self.subFrame = Frame(self, borderwidth=1, relief='groove', bg='white', padx=10)

        if default == 'open':
            self.show.set(1)
            self.subFrame.pack(fill='x', expand=1)
            self.toggleButton.configure(text='▼')
        elif default == 'closed':
            self.show.set(0)
            self.toggleButton.configure(text='▲')

    def toggle(self):
        if bool(self.show.get()):
            self.subFrame.pack(fill='x', expand=1)
            self.toggleButton.configure(text='▼')
        else:
            self.subFrame.forget()
            self.toggleButton.configure(text='▲')


# Context manager to patch joblib to report into tqdm progress bar given as argument
@contextlib.contextmanager
def tqdm_joblib(tqdm_object):
    class TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
        def __call__(self, *args, **kwargs):
            tqdm_object.update(n=self.batch_size)
            return super().__call__(*args, **kwargs)

    old_batch_callback = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
    try:
        yield tqdm_object
    finally:
        joblib.parallel.BatchCompletionCallBack = old_batch_callback
        tqdm_object.close()


# From a YAML file, insert the installation URL and API Token into curation script
# or return dictionary containing the information
def import_credentials(filePath, installationURLField=None, apiKeyField=None, forCurationApp=False):

    with open(filePath, 'r') as file:
        credentialsDict = yaml.safe_load(file)
        installationURL = credentialsDict['installationURL']
        apiKey = credentialsDict['apiToken']

    if forCurationApp is True:
        # Clear installationURLField and insert installationURL from YAML file
        installationURLField.set('')
        installationURLField.set(installationURL)

        # Clear apiKeyField and insert apiKey from YAML file
        apiKeyField.delete(0, END)
        apiKeyField.insert(END, apiKey)

    elif forCurationApp is False:
        return credentialsDict


def forget_widget(widget):
    exists = widget.winfo_exists()
    if exists == 1:
        widget.grid_forget()
    else:
        pass


# Function for getting value of nested key or returning nothing if nested key
# doesn't exist. If the value is a string, this truncates 
# the value to 10,000 characters, the character limit for many spreadsheet 
# applications, and replaces carriage returns with dashes
def improved_get(_dict, path, default=None):
    for key in path.split('.'):
        try:
            _dict = _dict[key]
        except KeyError:
            return default
    if isinstance(_dict, (int, dict, list)):
        return _dict
    elif isinstance(_dict, str):
        return _dict[:10000].replace('\r', ' - ')


def list_to_string(lst, delimiter=','):
    string = f'{delimiter} '.join(lst)
    return string


def string_to_list(string, delimiter=','):
    # If string has the characters of a list, e.g. enclosed by brackets, remove them first
    if string.startswith('['):
        string = string.replace('[', '').replace(']', '').replace('\'', '')
    stringToList = list(string.split(f'{delimiter}'))
    stringToList = [s.strip() for s in stringToList]
    return stringToList


def convert_to_local_tz(timestamp, shortDate=False):
    # Save local timezone to localTimezone variable
    localTimezone = tz.tzlocal()

    # If timestamp is a string, convert to datetime object
    if isinstance(timestamp, str):
        tzinfos = {'EDT': tz.gettz('US/Eastern')}
        timestamp = parse(timestamp, tzinfos=tzinfos)

    # Convert datetime to local timezone
    timestamp = timestamp.astimezone(localTimezone)

    if shortDate is True:
        # Return timestamp in YYYY-MM-DD format
        timestring = timestamp.strftime('%Y-%m-%d')
        timestamp = parse(timestring, tzinfos=tzinfos)

    return timestamp


# Makes bytes sizes more human-readable
def format_size(byteSize):
    if byteSize == 0:
        return '0 B'
    elif byteSize > 0:
       sizeName = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
       i = int(math.floor(math.log(byteSize, 1024)))
       p = math.pow(1024, i)
       s = round(byteSize / p, 2)
       sizeUnit = sizeName[i]
       return f'{s} {sizeUnit}'


# Converts timedelta object that shows a time duration as yy:mm:dd:hh:mm:ss,
# into more human readable string, e.g. 1 year, 8 months, 4 days...
def get_duration(timeDeltaObject):
    seconds = int(timeDeltaObject.total_seconds())

    if seconds < 1:
        return 'Less than 1 second'

    elif seconds == 1:
        return '1 second'

    elif seconds > 1:
        periods = [
            ('year', 60*60*24*365),
            ('month', 60*60*24*30),
            ('day', 60*60*24),
            ('hour', 60*60),
            ('minute', 60),
            ('second', 1)]

        strings = []
        for periodName, periodSeconds in periods:
            if seconds > periodSeconds:
                periodValue, seconds = divmod(seconds, periodSeconds)
                hasSeconds = 's' if periodValue > 1 else ''
                strings.append(f'{periodValue} {periodName}{hasSeconds}')

        return ', '.join(strings)


def divide_chunks(l, n):
    listOfLists = []
    for i in range(0, len(l), n):
        listOfLists.append(l[i:i + n])
    return listOfLists

def get_directory_path():
    directoryPath = filedialog.askdirectory()
    return directoryPath


def get_file_path(fileTypes):
    if 'yaml' in fileTypes:
        filePath = filedialog.askopenfilename(
            filetypes=[('YAML','*.yaml'), ('YAML', '*.yml')])
    return filePath


def select_all(listbox):
    listbox.select_set(0, END)


def clear_selections(listbox):
    listbox.selection_clear(0, END)


def check_installation_url_status(string, requestTimeout=20, headers={}):
    statusDict = {}

    if string.startswith('http'):
        parsed = urlparse(string)
        installationUrl = parsed.scheme + '://' + parsed.netloc

        try:
            response = requests.get(installationUrl, headers=headers, timeout=requestTimeout, verify=False)
            parsed = urlparse(response.url)
            statusDict['statusCode'] = response.status_code
            statusDict['installationUrl'] = parsed.scheme + '://' + parsed.netloc
        except Exception as e:
            statusDict['statusCode'] = f'ERROR: {e}'
            statusDict['installationUrl'] = parsed.scheme + '://' + parsed.netloc

    elif '(' in string:
        installationUrl = re.search(r'\(.*\)', string).group()
        installationUrl = re.sub('\(|\)', '', installationUrl)
        # Use requests to get the final redirect URL. At least on installation, sodha, redirects to www.sodha.be
        try:
            installationUrl = requests.get(installationUrl, timeout=requestTimeout, verify=False).url
            parsed = urlparse(installationUrl)
            statusDict['statusCode'] = response.status_code
            statusDict['installationUrl'] = parsed.scheme + '://' + parsed.netloc

        except Exception as e:
            statusDict['statusCode'] = 'ERROR'
            statusDict['installationUrl'] = parsed.scheme + '://' + parsed.netloc

    return statusDict


# Gets list of URLs from Dataverse map JSON data and add Demo Dataverse url
def get_installation_list():
    installationsList = []
    dataverseInstallationsJsonUrl = 'https://raw.githubusercontent.com/IQSS/dataverse-installations/main/data/data.json'
    response = requests.get(dataverseInstallationsJsonUrl)
    data = response.json()

    for installation in data['installations']:
        name = installation['name']
        hostname = installation['hostname']
        installationUrl = 'https://' + hostname
        nameAndUrl = f'{name} ({installationUrl})'
        installationsList.append(nameAndUrl)

    installationsList.insert(0, 'Demo Dataverse (https://demo.dataverse.org)')

    return installationsList


def check_api_endpoint(url, headers, verify=False, json_response_expected=True):
    try:
        response = requests.get(url, headers=headers, timeout=20, verify=verify)
        if response.status_code == 200:
            status = 'OK'
        elif response.status_code != 200:
            if json_response_expected is True:
                try:
                    data = response.json()
                    statusCode = data['status']
                    statusMessage = data['message']
                    status = f'{statusCode}: {statusMessage}'
                except Exception as e:
                    status = e
            elif json_response_expected is False:
                status = response.status_code
    except Exception as e:
        status = e

    return status


def sanitize_version(version):
    # Specifically look for a major/minor semver-formatted version
    # https://stackoverflow.com/questions/15340582/python-extract-pattern-matches
    # Adapted from code by Goeff Thomas. See https://www.kaggle.com/code/goefft/check-dataverse-installation-versions
    result = re.compile('(\d+\.)?(\d+\.)?(\*|\d+)').search(version)
    if result is None:
        return 'NA'
    return result.group()


# Write function that checks version of Dataverse installation
def get_dataverse_installation_version(installationUrl, headers={}):
    installationVersionDict = {}
    statusDict = check_installation_url_status(string=installationUrl, requestTimeout=20, headers=headers)
    statusCode = statusDict['statusCode']

    if statusCode != 200:
        installationVersionDict['dataverseVersion'] = statusCode
        installationVersionDict['dataverseVersionSanitized'] = statusCode

    elif statusCode == 200:
        installationUrl = statusDict['installationUrl']

        getInstallationVersionApiUrl = f'{installationUrl}/api/v1/info/version'
        getInstallationVersionApiUrl = getInstallationVersionApiUrl.replace('//api', '/api')
        response = requests.get(getInstallationVersionApiUrl, headers=headers, timeout=20, verify=False)
        data = response.json()
        dataverseVersion = data['data']['version']

        dataverseVersionSanitized = sanitize_version(dataverseVersion)

        installationVersionDict = {
            'dataverseVersion': dataverseVersion,
            'dataverseVersionSanitized': dataverseVersionSanitized
        }

    return installationVersionDict


def get_root_alias(url, headers={}):
    # Function for getting name of installation's root collection 
    if '/dataverse/' in url:
        parsed = urlparse(url)
        url = f'{parsed.scheme}://{parsed.netloc}/api/dataverses/:root'
        url = url.replace('//api', '/api')
        response = requests.get(url, headers=headers)
        dataverseData = response.json()
        rootAlias = dataverseData['data']['alias']
    elif '/dataverse/' not in url:
        url = f'{url}/api/dataverses/:root'
        url = url.replace('//api', '/api')
        response = requests.get(url, headers=headers, verify=False)
        dataverseData = response.json()
        rootAlias = dataverseData['data']['alias']

    return rootAlias


# Function for getting collection alias name of a given Dataverse Collection URL,
# including the "Root" collection
def get_alias_from_collection_url(url, headers={}):

    # If /dataverse/ is not in the URL, assume it's the installation's server url...
    if '/dataverse/' not in url:
        # If it's the UVA homepage URL, get it's root alias, whose database ID is not 1
        if 'dataverse.lib.virginia.edu' in url:
            alias = 'uva'

        # If's it's not the UVA homepage URL, get the alias of the collection whose database is 1
        elif 'dataverse.lib.virginia.edu' not in url:
            installationStatusDict = check_installation_url_status(url, headers=headers)
            installationUrl = installationStatusDict['installationUrl']
            url = f'{installationUrl}/api/dataverses/1'
            response = requests.get(url, headers=headers, verify=False)
            dataverseData = response.json()
            alias = dataverseData['data']['alias']

    # If /dataverse/ is in the url, assume it's a collection URL and parse string to get its alias...
    elif '/dataverse/' in url:
        parsed = urlparse(url)
        try:
            alias = parsed.path.split('/')[2]
        # Or return an empty string
        except IndexError:
            alias = ''

    return alias


# Returns True if collection alias is the installation's root collection or
# False if not (doesn't work with UVA)
def is_root_collection(url, headers={}):
    if get_alias_from_collection_url(url, headers=headers) == get_root_alias(url, headers=headers):
        return True
    elif get_alias_from_collection_url(url) != get_root_alias(url):
        return False


# Function that turns Dataverse installation URL, instalation URL or search URL into a Search API URL
def get_search_api_url(url):

    # If URL is not a search url (doesn't contain 'q=') and contains /dataverse/, it's a Dataverse collection URL
    if 'q=' not in url and '/dataverse/' in url:
        # Remove the jsessionidString that sometimes appears in the URL
        try:
            jsessionidString = re.search(r';jsessionid=.*', url).group()
            url = url.replace(jsessionidString, '?')
        except AttributeError:
            pass
        # Get the Dataverse Collection name in the search URL
        dataversePart = re.search(r'\/dataverse\/.*', url).group()
        dataverseName = dataversePart.replace('/dataverse/', '')
        # Repalce '/dataverse/' and the dataverse name with '/api/search?q=*' and add subtree parameter with dataverse name
        apiSearchURL = url.replace(dataversePart, '/api/search?q=*') + f'&subtree={dataverseName}'
        apiSearchURL = apiSearchURL.rstrip('?')

    # If URL is not a search URL (doesn't contain 'q=') and doesn't have /dataverse/, assume it's the URL of the installation
    if 'q=' not in url and '/dataverse/' not in url:
        apiSearchURL = url.replace('/dataverse.xhtml', '')
        apiSearchURL = apiSearchURL + '/api/search'
        # If entered installation URL ends with a forward slash, replace resulting double slash with a single slash
        apiSearchURL = apiSearchURL.replace('//api', '/api') + '?q=*'

    # If URL has 'q=', then assume it's a Search URL
    elif 'q=' in url:

        # Sometimes there's a slash before the ?q. If so, remove it
        url = url.replace('/?q', '?q')

        # If there's a jsessionid string, remove it
        try:
            jsessionidString = re.search(r';jsessionid=.*\?', url).group()
            url = url.replace(jsessionidString, '?')
        except AttributeError:
            pass
        
        # Get the Dataverse Collection name in the search URL
        # dataverseName = re.search(r'\/dataverse\/\w*\?q', url)
        dataverseName = re.search(r'\/dataverse\/.*\?q', url)
        dataverseName = dataverseName.group()

        subtree = dataverseName.replace('/dataverse/', '&subtree=').replace('?q', '')

        apiSearchURL = (
            url
                .replace(dataverseName, '/api/search?q')
                .replace('?q=&', '?q=*&')
                .replace('%3A', ':')
                .replace('%22', '"')
                .replace('%28', '(')
                .replace('%29', ')')
                + '&show_entity_ids=true'
                + subtree
                )

        # Remove any digits after any fq parameters
        apiSearchURL = re.sub('fq\d', 'fq', apiSearchURL)

        apiSearchURL = apiSearchURL + '&per_page=10&start=0'

        # Replace values of any "types" parameters in the Search API's "type" paramater
        try:
            dTypes = re.search(r'types=.*?&', apiSearchURL).group()
            dTypesList = dTypes.replace('types=', '').replace('&', '').split(':')
            dTypesString = ''
            for dType in dTypesList:
                dType = '&type=%s' %(re.sub('s$', '', dType))
                dTypesString = dTypesString + dType
            apiSearchURL = apiSearchURL + dTypesString
        except AttributeError:
            pass

        # Remove dvObjectType and types parameters, which I think the Search API is ignoring
        apiSearchURL = re.sub('fq=dvObjectType:\(.*\)&', '', apiSearchURL)
        apiSearchURL = re.sub('types=.*?&', '', apiSearchURL)

    return apiSearchURL


# Function that converts as many common html codes as I could find into their human-readable strings
def convert_str_to_html_encoding(string):
    string = (
        string
            .replace('%20', ' ').replace('%21', '!').replace('%22', '\"').replace('%23', '#')
            .replace('%24', '$').replace('%25', '%').replace('%26', '&').replace('%27', '\'')
            .replace('%28', '(').replace('%29', ')').replace('%2A', '*').replace('%2B', '+')
            .replace('%2C', ',').replace('%2D', '-').replace('%2E', '.').replace('%2F', '/')
            .replace('%30', '0').replace('%31', '1').replace('%32', '2').replace('%33', '3')
            .replace('%34', '4').replace('%35', '5').replace('%36', '6').replace('%37', '7')
            .replace('%38', '8').replace('%39', '9').replace('%3A', ':').replace('%3B', ';')
            .replace('%3C', '<').replace('%3D', '=').replace('%3E', '>').replace('%3F', '?')
            .replace('%40', '@').replace('%41', 'A').replace('%42', 'B').replace('%43', 'C')
            .replace('%44', 'D').replace('%45', 'E').replace('%46', 'F').replace('%47', 'G')
            .replace('%48', 'H').replace('%49', 'I').replace('%4A', 'J').replace('%4B', 'K')
            .replace('%4C', 'L').replace('%4D', 'M').replace('%4E', 'N').replace('%4F', 'O')
            .replace('%50', 'P').replace('%51', 'Q').replace('%52', 'R').replace('%53', 'S')
            .replace('%54', 'T').replace('%55', 'U').replace('%56', 'V').replace('%57', 'W')
            .replace('%58', 'X').replace('%59', 'Y').replace('%5A', 'Z').replace('%5B', '[')
            .replace('%5C', '\\').replace('%5D', ']').replace('%5E', '^').replace('%5F', '_')
            .replace('%60', '`').replace('%61', 'a').replace('%62', 'b').replace('%63', 'c')
            .replace('%64', 'd').replace('%65', 'e').replace('%66', 'f').replace('%67', 'g')
            .replace('%68', 'h').replace('%69', 'i').replace('%6A', 'j').replace('%6B', 'k')
            .replace('%6C', 'l').replace('%6D', 'm').replace('%6E', 'n').replace('%6F', 'o')
            .replace('%70', 'p').replace('%71', 'q').replace('%72', 'r').replace('%73', 's')
            .replace('%74', 't').replace('%75', 'u').replace('%76', 'v').replace('%77', 'w')
            .replace('%78', 'x').replace('%79', 'y').replace('%7A', 'z').replace('%7B', '{')
            .replace('%7C', '|').replace('%7D', '}').replace('%7E', '~').replace('%80', '€')
            .replace('%82', '‚').replace('%83', 'ƒ').replace('%84', '„').replace('%85', '…')
            .replace('%86', '†').replace('%87', '‡').replace('%88', 'ˆ').replace('%89', '‰')
            .replace('%8A', 'Š').replace('%8B', '‹').replace('%8C', 'Œ').replace('%8E', 'Ž')
            .replace('%91', '‘').replace('%92', '’').replace('%93', '“').replace('%94', '”')
            .replace('%95', '•').replace('%96', '–').replace('%97', '—').replace('%98', '˜')
            .replace('%99', '™').replace('%9A', 'š').replace('%9B', '›').replace('%9C', 'œ')
            .replace('%9E', 'ž').replace('%9F', 'Ÿ').replace('%A1', '¡').replace('%A2', '¢')
            .replace('%A3', '£').replace('%A4', '¤').replace('%A5', '¥').replace('%A6', '¦')
            .replace('%A7', '§').replace('%A8', '¨').replace('%A9', '©').replace('%AA', 'ª')
            .replace('%AB', '«').replace('%AC', '¬').replace('%AE', '®').replace('%AF', '¯')
            .replace('%B0', '°').replace('%B1', '±').replace('%B2', '²').replace('%B3', '³')
            .replace('%B4', '´').replace('%B5', 'µ').replace('%B6', '¶').replace('%B7', '·')
            .replace('%B8', '¸').replace('%B9', '¹').replace('%BA', 'º').replace('%BB', '»')
            .replace('%BC', '¼').replace('%BD', '½').replace('%BE', '¾').replace('%BF', '¿')
            .replace('%C0', 'À').replace('%C1', 'Á').replace('%C2', 'Â').replace('%C3', 'Ã')
            .replace('%C4', 'Ä').replace('%C5', 'Å').replace('%C6', 'Æ').replace('%C7', 'Ç')
            .replace('%C8', 'È').replace('%C9', 'É').replace('%CA', 'Ê').replace('%CB', 'Ë')
            .replace('%CC', 'Ì').replace('%CD', 'Í').replace('%CE', 'Î').replace('%CF', 'Ï')
            .replace('%D0', 'Ð').replace('%D1', 'Ñ').replace('%D2', 'Ò').replace('%D3', 'Ó')
            .replace('%D4', 'Ô').replace('%D5', 'Õ').replace('%D6', 'Ö').replace('%D7', '×')
            .replace('%D8', 'Ø').replace('%D9', 'Ù').replace('%DA', 'Ú').replace('%DB', 'Û')
            .replace('%DC', 'Ü').replace('%DD', 'Ý').replace('%DE', 'Þ').replace('%DF', 'ß')
            .replace('%E0', 'à').replace('%E1', 'á').replace('%E2', 'â').replace('%E3', 'ã')
            .replace('%E4', 'ä').replace('%E5', 'å').replace('%E6', 'æ').replace('%E7', 'ç')
            .replace('%E8', 'è').replace('%E9', 'é').replace('%EA', 'ê').replace('%EB', 'ë')
            .replace('%EC', 'ì').replace('%ED', 'í').replace('%EE', 'î').replace('%EF', 'ï')
            .replace('%F0', 'ð').replace('%F1', 'ñ').replace('%F2', 'ò').replace('%F3', 'ó')
            .replace('%F4', 'ô').replace('%F5', 'õ').replace('%F6', 'ö').replace('%F7', '÷')
            .replace('%F8', 'ø').replace('%F9', 'ù').replace('%FA', 'ú').replace('%FB', 'û')
            .replace('%FC', 'ü').replace('%FD', 'ý').replace('%FE', 'þ').replace('%FF', 'ÿ')
        )
    return string


def convert_utf8bytes_to_characters(string):
    string = (
        string
            .replace('%E2%82%AC', '€').replace('%E2%80%9A', '‚').replace('%C6%92', 'ƒ')
            .replace('%E2%80%A6', '…').replace('%E2%80%A0', '†').replace('%E2%80%A1', '‡')
            .replace('%E2%80%B0', '‰').replace('%C5%A0', 'Š').replace('%E2%80%B9', '‹')
            .replace('%C5%BD', 'Ž').replace('%E2%80%98', '‘').replace('%E2%80%99', '’')
            .replace('%E2%80%9D', '”').replace('%E2%80%A2', '•').replace('%E2%80%93', '–')
            .replace('%CB%9C', '˜').replace('%E2%84%A2', '™').replace('%C5%A1', 'š')
            .replace('%C5%93', 'œ').replace('%C5%BE', 'ž').replace('%C5%B8', 'Ÿ')
            .replace('%C2%A2', '¢').replace('%C2%A3', '£').replace('%C2%A4', '¤')
            .replace('%C2%A6', '¦').replace('%C2%A7', '§').replace('%C2%A8', '¨')
            .replace('%C2%AA', 'ª').replace('%C2%AB', '«').replace('%C2%AC', '¬')
            .replace('%C2%AE', '®').replace('%C2%AF', '¯').replace('%C2%B0', '°')
            .replace('%C2%B2', '²').replace('%C2%B3', '³').replace('%C2%B4', '´')
            .replace('%C2%B6', '¶').replace('%C2%B7', '·').replace('%C2%B8', '¸')
            .replace('%C2%BA', 'º').replace('%C2%BB', '»').replace('%C2%BC', '¼')
            .replace('%C2%BE', '¾').replace('%C2%BF', '¿').replace('%C3%80', 'À')
            .replace('%C3%82', 'Â').replace('%C3%83', 'Ã').replace('%C3%84', 'Ä')
            .replace('%C3%86', 'Æ').replace('%C3%87', 'Ç').replace('%C3%88', 'È')
            .replace('%C3%8A', 'Ê').replace('%C3%8B', 'Ë').replace('%C3%8C', 'Ì')
            .replace('%C3%8E', 'Î').replace('%C3%8F', 'Ï').replace('%C3%90', 'Ð')
            .replace('%C3%92', 'Ò').replace('%C3%93', 'Ó').replace('%C3%94', 'Ô')
            .replace('%C3%96', 'Ö').replace('%C3%97', '×').replace('%C3%98', 'Ø')
            .replace('%C3%9A', 'Ú').replace('%C3%9B', 'Û').replace('%C3%9C', 'Ü')
            .replace('%C3%9E', 'Þ').replace('%C3%9F', 'ß').replace('%C3%A0', 'à')
            .replace('%C3%A2', 'â').replace('%C3%A3', 'ã').replace('%C3%A4', 'ä')
            .replace('%C3%A6', 'æ').replace('%C3%A7', 'ç').replace('%C3%A8', 'è')
            .replace('%C3%AA', 'ê').replace('%C3%AB', 'ë').replace('%C3%AC', 'ì')
            .replace('%C3%8D', 'Í').replace('%C3%AE', 'î').replace('%C3%AF', 'ï')
            .replace('%C3%B0', 'ð').replace('%C3%B2', 'ò').replace('%C3%B3', 'ó')
            .replace('%C3%B4', 'ô').replace('%C3%B6', 'ö').replace('%C3%B7', '÷')
            .replace('%C3%B8', 'ø').replace('%C3%BA', 'ú').replace('%C3%BB', 'û')
            .replace('%C3%BC', 'ü').replace('%C3%BE', 'þ').replace('%C3%BF', 'ÿ')
        )
    return string


def search_api_includes_metadata_fields(installationUrl, headers={}):
    statusDict = check_installation_url_status(installationUrl, requestTimeout=20, headers=headers)
    installationUrl = statusDict['installationUrl']
    searchApiUrl = f'{installationUrl}/api/search?q=*&type=dataset&metadata_fields=citation:title&per_page=1'
    response = requests.get(searchApiUrl, headers=headers, timeout=60, verify=False)
    data = response.json()

    if data['status'] != 'OK':
        return data['status']

    elif data['status'] == 'OK' and data['data']['total_count'] == 0:
        return 'No published datasets found'

    elif data['status'] == 'OK' and data['data']['total_count'] > 0:
        if 'metadataBlocks' in data['data']['items'][0]:
            return True
        else:
            return False


# Function that returns the params of a given Search API URL, to be used in requests calls
def get_params(apiSearchURL, metadataFieldsList=None):
    params = {
        'baseUrl': '',
        'params': {}
    }
    fq = []

    # Split apiSearchURL to create list of params
    splitSearchURLList = re.split('\?q|&fq|&', apiSearchURL)

    # Remove base search API URL from list
    params['baseUrl'] = splitSearchURLList[0]
    splitSearchURLList.pop(0)

    # Remove any empty items from the splitSearchURLList
    splitSearchURLList = list(filter(None, splitSearchURLList))

    # Re-add the q that starts the query paramters
    splitSearchURLList[0] = 'q' + splitSearchURLList[0]

    typeParamList = []

    for paramValue in splitSearchURLList:

        # Add query to params dict
        if paramValue.startswith('q='):
            paramValue = convert_utf8bytes_to_characters(paramValue)
            paramValue = convert_str_to_html_encoding(paramValue)
            paramValue = paramValue.replace('+', ' ')
            params['params']['q'] = paramValue.replace('q=', '')

        # Add non-fq queries to params dict
        if not paramValue.startswith('=') and not paramValue.startswith('q='):
            key = paramValue.split('=')[0]
            if paramValue.split('=')[1] != '':
                params['params'][key] = paramValue.split('=')[1]

        # Add values of each type param to typeParamList
        if paramValue.startswith('type'):
            valueString = paramValue.split('=')[1]
            typeParamList.append(valueString)

        # Add fq queries to fq dict if paramValue.startswith('='):
        if paramValue.startswith('='):
            key = paramValue.replace('=', '').split(':')[0]
            value = paramValue.split(':')[1]
            value = convert_utf8bytes_to_characters(value)
            value = convert_str_to_html_encoding(value)
            value = value.replace('+', ' ')
            paramString = key + ':' + value
            fq.append(paramString)

    # If there are type param values in typeParamList, add as value to new "type" param
    if typeParamList:
        params['params']['type'] = typeParamList

    # If there are any fq params, add fq keys and values
    if len(fq) > 0:
        params['params']['fq'] = fq

    if metadataFieldsList is not None:
        if len(metadataFieldsList) > 5:
            print('Function supports only five parent metadata fields. Remove fields.')
            exit()
        elif len(metadataFieldsList) < 6:
            params['params']['metadata_fields'] = metadataFieldsList

    return params


# Gets info from Search API about a given dataverse, dataset or file
def get_value_row_from_search_api_object(item, installationUrl, metadataFieldsList=None):
    
    if metadataFieldsList is not None and item['type'] == 'dataset':

        newRow = {
            'dataset_pid': item['global_id'],
            'version_state': item['versionState'],
            'dataset_version_create_time': item['createdAt'],
            'file_count': improved_get(item, 'fileCount'),
            'dataverse_collection_alias': item['identifier_of_dataverse'],
            'dataverse_name': item['name_of_dataverse']
        }

        # Get value of metadata field and add to newRow dict.
        # Value may be a string, list or dict, depending on type of metadata field
        for metadataField in metadataFieldsList:

            metadatablockName = metadataField.split(':')[0]
            parentFieldName = metadataField.split(':')[1]
            
            # If the metadata block is in the item and there are fields, add the field values to the newRow Dict
            if metadatablockName in item['metadataBlocks'] and len(item['metadataBlocks'][metadatablockName]['fields']) > 0:
                metadataBlockFieldsDict = item['metadataBlocks'][metadatablockName]['fields']
                for field in metadataBlockFieldsDict:
                    if field['typeName'] == parentFieldName:
                        newRow[metadataField] = field['value']

        return newRow

    elif metadataFieldsList is None:

        if item['type'] == 'dataset':

            versionState = item['versionState']
            if versionState == 'DRAFT':
                latestVersionNumber = 'DRAFT'
            elif versionState == 'DEACCESSIONED':
                latestVersionNumber = 'DEACCESSIONED'
            elif versionState == 'RELEASED':
                majorVersionNumber = item['majorVersion']
                minorVersionNumber = item['minorVersion']
                latestVersionNumber = f'{majorVersionNumber}.{minorVersionNumber}'

            newRow = {
                'dataset_pid': item['global_id'],
                'version_state': item['versionState'],
                'latest_version': latestVersionNumber,
                'dataset_version_create_time': item['createdAt'],
                'publication_date': improved_get(item, 'published_at'),
                'file_count': improved_get(item, 'fileCount'),
                'dataverse_collection_alias': item['identifier_of_dataverse'],
                'dataverse_name': item['name_of_dataverse']
            }
        
        if item['type'] == 'dataverse':
            newRow = {
                'dataverse_database_id': item['entity_id'],
                'dataverse_collection_alias': item['identifier'],
                'dataverse_url': item['url'],
                'dataverse_name': item['name'],
                'dataverse_description': improved_get(item, 'description')
            }
        if item['type'] == 'file':
            filePersistentId = improved_get(item, 'file_persistent_id', default='')
            
            newRow = {
                'file_database_id': item['file_id'],
                'file persistent_id': filePersistentId,
                'file_name': item['name'],
                'dataset_pid': item['dataset_persistent_id']
            }
    
        return newRow


def get_object_dictionary_from_search_api_page(
    installationUrl, headers, params, start, 
    objectInfoDict, metadataFieldsList=None):
    searchApiUrl = f'{installationUrl}/api/search'
    params['start'] = start
    params['per_page'] = 10
    response = requests.get(
        searchApiUrl,
        params=params,
        headers=headers,
        verify=False
    )
    data = response.json()

    if metadataFieldsList is not None:
        for item in data['data']['items']:
            if item['type'] == 'dataset':
                newRow = get_value_row_from_search_api_object(item, installationUrl, metadataFieldsList=metadataFieldsList)
                objectInfoDict.append(dict(newRow))

    elif metadataFieldsList is None:
        for item in data['data']['items']:
            newRow = get_value_row_from_search_api_object(item, installationUrl, metadataFieldsList=metadataFieldsList)
            objectInfoDict.append(dict(newRow))

    sleep(1)


# Get variables for the Search API's "start" parameter to paginate through search results
def get_search_api_start_list(itemCount):
    start = 0
    apiCallsCount = math.ceil(itemCount/10) - 1
    startsList = [0]
    for apiCall in range(apiCallsCount):
        start = start + 10
        startsList.append(start)
    startsListCount = len(startsList)

    startInfo = {
        'startsListCount': startsListCount,
        'startsList': startsList
    }

    return startInfo


# Uses Search API to return dataframe containing info about collectoins, datasets or files in an installation
# Write results to the tkinter window
def get_object_dataframe_from_search_api(
    baseUrl, params, objectType, headers={}, metadataFieldsList=None,
    printProgress=False, rootWindow=None, progressText=None,
    progressLabel=None, apiKey=None):

    installationStatusDict = check_installation_url_status(baseUrl)
    installationUrl = installationStatusDict['installationUrl']

    if apiKey:
        headers['X-Dataverse-key'] = apiKey

    params['type'] = objectType

    # Add param to show database IDs of each item
    params['show_entity_ids'] = 'true'

    # Get total count of objects
    params['per_page'] = 1

    response = requests.get(
        baseUrl,
        params=params,
        headers=headers,
        verify=False
    )
    data = response.json()

    if data['status'] == 'ERROR':
        text = 'Search API error. Check URL or API key'
        print(text)

        if None not in [rootWindow, progressText, progressLabel]:
            progressText.set(text)
            progressLabel.config(fg='green')
            progressLabel = progressLabel.grid(sticky='w', row=0)
            rootWindow.update_idletasks()

    elif data['status'] == 'OK':
        totalDatasetCount = data['data']['total_count']
        text = 'Looking for datasets...'

        if None not in [rootWindow, progressText, progressLabel]:
            progressText.set(text)
            progressLabel.config(fg='green')
            progressLabel = progressLabel.grid(sticky='w', row=0)
            rootWindow.update_idletasks()
        
        # Create start variables to paginate through Search API results
        startInfo = get_search_api_start_list(totalDatasetCount)
        startsListCount = startInfo['startsListCount']
        startsList = startInfo['startsList']

        # misindexedObjectCount = 0
        objectInfoDict = []

        if None not in [rootWindow, progressText, progressLabel]:
            for start in startsList:
                get_object_dictionary_from_search_api_page(
                    installationUrl, headers, params, start, objectInfoDict, metadataFieldsList)

        else:
            for start in (pbar := tqdm(startsList, bar_format=tqdm_bar_format)):
                pbar.set_description(f'Page {start}')

                get_object_dictionary_from_search_api_page(
                    installationUrl, headers, params, start, objectInfoDict, metadataFieldsList)

        objectInfoDF = pd.DataFrame(objectInfoDict)

        return objectInfoDF


# Uses "Get Contents" endpoint to return list of dataverse aliases of all subcollections in a given collection
def get_all_subcollection_aliases(collectionUrl, headers={}, apiKey=''):

    parsed = urlparse(collectionUrl)
    installationUrl = parsed.scheme + '://' + parsed.netloc
    alias = parsed.path.split('/')[2]

    if apiKey:
        headers['X-Dataverse-key'] = apiKey

    # Get ID of given dataverse alias
    dataverseInfoEndpoint = f'{installationUrl}/api/dataverses/{alias}'

    response = requests.get(
        dataverseInfoEndpoint,
        headers=headers,
        verify=False)
    data = response.json()
    parentDataverseId = data['data']['id']

    # Create list and add ID of given dataverse
    dataverseIds = [parentDataverseId]

    # Get each subdataverse in the given dataverse
    for dataverseId in dataverseIds:
        dataverseGetContentsEndpoint = f'{installationUrl}/api/dataverses/{dataverseId}/contents'
        response = requests.get(
            dataverseGetContentsEndpoint,
            headers=headers)
        data = response.json()

        for item in data['data']:
            if item['type'] == 'dataverse':
                dataverseId = item['id']
                dataverseIds.extend([dataverseId])

    # Get the alias for each dataverse ID
    dataverseAliases = []
    for dataverseId in dataverseIds:
        dataverseInfoEndpoint = f'{installationUrl}/api/dataverses/{dataverseId}'
        response = requests.get(
            dataverseInfoEndpoint,
            headers=headers)
        data = response.json()
        alias = data['data']['alias']
        dataverseAliases.append(alias)

    return dataverseAliases


def get_collection_info(installationUrl, alias, dataverseCollectionInfoDict, headers={}, apiKey='', verify=False):

    try:
        viewCollectionApiEndpointURL = f'{installationUrl}/api/dataverses/{alias}'
        response = requests.get(
            viewCollectionApiEndpointURL,
            headers=headers,
            verify=verify)
        data = response.json()

        if data['status'] == 'ERROR':
            creationDate = 'NA'
            contactEmailsString = 'NA'
            dataverseType = 'NA'

        elif data['status'] == 'OK':
            creationDate = convert_to_local_tz(data['data']['creationDate'], shortDate=True)
            
            dataverseContacts = improved_get(data, 'data.dataverseContacts')
            if dataverseContacts is None:
                contactEmailsString = 'NA'
            elif dataverseContacts is not None:
                contactEmailsList = []
                for dataverseContact in data['data']['dataverseContacts']:
                    contactEmail = dataverseContact['contactEmail']
                    contactEmailsList.append(contactEmail)
                contactEmailsString = list_to_string(contactEmailsList)
            dataverseType = data['data']['dataverseType']

        newRow = {
            'dataverse_collection_alias': alias,
            'dataverse_collection_create_date': creationDate,
            'dataverse_collection_contact_emails': contactEmailsString,
            'dataverse_collection_type': dataverseType
            }
        # dataverseCollectionInfoDict.append(dict(newRow))

    except Exception as e:
        print(f'\t{e}')
        newRow = {
            'dataverse_collection_alias': alias,
            'dataverse_collection_create_date': 'NA',
            'dataverse_collection_contact_emails': 'NA',
            'dataverse_collection_type': 'NA'
            }
    dataverseCollectionInfoDict.append(dict(newRow))


def get_collections_info(installationUrl, aliasList, dataverseCollectionInfoDict, headers, apiKey=''):
    aliasCount = len(aliasList)

    # Use joblib library to use 4 CPU cores to make SearchAPI calls to get info about datasets
    # and report progress using tqdm progress bars
    with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=aliasCount)) as progress_bar:
        Parallel(n_jobs=4, backend='threading')(delayed(get_collection_info)(
            installationUrl,
            alias,
            dataverseCollectionInfoDict,
            headers,
            apiKey) for alias in aliasList)


def get_canonical_pid(pidOrUrl):

    # If entered dataset PID is the dataset page URL, get canonical PID
    if pidOrUrl.startswith('http') and 'persistentId=' in pidOrUrl:
        canonicalPid = pidOrUrl.split('persistentId=')[1]
        canonicalPid = canonicalPid.split('&version')[0]
        canonicalPid = canonicalPid.replace('%3A', ':').replace('%2F', ('/'))

    # If entered dataset PID is a DOI URL, get canonical PID
    elif pidOrUrl.startswith('http') and 'doi.' in pidOrUrl:
        canonicalPid = re.sub('http.*org\/', 'doi:', pidOrUrl)

    # If entered dataset PID is a canonical DOI, save it as canonicalPid
    elif pidOrUrl.startswith('doi:') and '/' in pidOrUrl:
        canonicalPid = pidOrUrl

    # If entered dataset PID is a Handle URL, get canonical PID
    elif pidOrUrl.startswith('http') and 'hdl.' in pidOrUrl:
        canonicalPid = re.sub('http.*net\/', 'hdl:', pidOrUrl)

    # If entered dataset PID is a canonical HDL, save it as canonicalPid
    elif pidOrUrl.startswith('hdl:') and '/' in pidOrUrl:
        canonicalPid = pidOrUrl

    else:
        canonicalPid = pidOrUrl

    return canonicalPid


def get_url_form_of_pid(canonicalPid, installationUrl):
    if canonicalPid.startswith('doi:'):
        pidUrlForm = canonicalPid.replace('doi:', 'https://doi.org/')

    elif canonicalPid.startswith('hdl:'):
        pidUrlForm = canonicalPid.replace('hdl:', 'https://hdl.handle.net/')

    else:
        pidUrlForm = f'{installationUrl}/dataset.xhtml?persistentId={canonicalPid}'

    return pidUrlForm

def get_datasets_from_collection_or_search_url(
    url, headers={}, rootWindow=None, progressLabel=None, progressText=None, textBoxCollectionDatasetPIDs=None, 
    apiKey='', ignoreDeaccessionedDatasets=False, subdataverses=False):

    # Hide the textBoxCollectionDatasetPIDs scrollbox if it exists
    if textBoxCollectionDatasetPIDs is not None:
        forget_widget(textBoxCollectionDatasetPIDs)
    
    # Use the Search API to get dataset info from the given search url or Dataverse collection URL
    url = url.rstrip('/')
    searchApiUrl = get_search_api_url(url)

    requestsGetProperties = get_params(searchApiUrl)
    baseUrl = requestsGetProperties['baseUrl']
    params = requestsGetProperties['params']

    datasetInfoDF = get_object_dataframe_from_search_api(
        baseUrl=baseUrl, params=params, headers=headers, objectType='dataset', metadataFieldsList=None,
        printProgress=False, rootWindow=rootWindow, progressText=progressText, 
        progressLabel=progressLabel, apiKey=apiKey)

    # If get_object_dataframe_from_search_api doesn't return a dataframe, there was an error 
    if not isinstance(datasetInfoDF, pd.DataFrame):
        text = 'Search API error. Check URL or API key'
        if progressText is not None:
            progressText.set(text)
        else:
            print(text)

    elif isinstance(datasetInfoDF, pd.DataFrame):
        datasetCount = len(datasetInfoDF.index)

        if datasetCount == 0:
            text = 'Datasets found: 0'

            if progressText is not None:
                progressText.set(text)
            else:
                print(text)
        
        elif datasetCount > 0:

            deaccessionedDatasetCount = 0
            
            # To ignore deaccessioned datasets, remove from the dataframe all datasets where version_state is DEACCESSIONED 
            if ignoreDeaccessionedDatasets == True:
                datasetInfoDF = datasetInfoDF[datasetInfoDF['version_state'].str.contains('DEACCESSIONED') == False]
                deaccessionedDatasetCount = datasetCount - len(datasetInfoDF.index)

            # Remove version_state column so that I can remove the dataframe's duplicate rows and there's only one row per dataset
            datasetInfoDF = datasetInfoDF.drop('version_state', axis=1)

            # Drop duplicate rows, which happens when Search API results lists a dataset's published and draft versions
            datasetInfoDF = datasetInfoDF.drop_duplicates()

            # Recount datasets
            uniqueDatasetCount = len(datasetInfoDF.index)

            # Check if url is collection url. If so:
            if 'q=' not in url:
                # If the user wants datasets in all subdataverses and the url
                # is the root collection, don't filter the dataframe
                if subdataverses == True and is_root_collection(url, headers=headers) == True:
                    uniqueDatasetCount = len(datasetInfoDF)

                # If the user wants datasets in all subdataverses and the url
                # is not the root collection...
                elif subdataverses == True and is_root_collection(url, headers=headers) == False:
                    # Get the aliases of all subdataverses...
                    dataverseAliases = get_all_subcollection_aliases(url, apiKey=apiKey)

                    # Remove any datasets that aren't owned by any of the 
                    # subdataverses. This will exclude linked datasets
                    datasetInfoDF = datasetInfoDF[
                        datasetInfoDF['dataverse_collection_alias'].isin(dataverseAliases)]

                    uniqueDatasetCount = len(datasetInfoDF)

                # If the user wants only datasets in the collection,
                # and not in collections within the collection...
                elif subdataverses == False:
                    # Get the alias of the collection (including the alias of the root collection)
                    alias = get_alias_from_collection_url(url, headers=headers)
                    # Retain only datasets owned by that collection
                    datasetInfoDF = datasetInfoDF[datasetInfoDF['dataverse_collection_alias'].isin([alias])]

                    uniqueDatasetCount = len(datasetInfoDF)

            # If the url is a search URL, get all datasetPids from datasetInfoDF 
            elif 'q=' in url:
                uniqueDatasetCount = len(datasetInfoDF)

            if textBoxCollectionDatasetPIDs is not None:
                # Place textbox with list of dataset PIDs and set state to read/write (normal) 
                textBoxCollectionDatasetPIDs.grid(sticky='w', row=2, pady=5)
                textBoxCollectionDatasetPIDs.configure(state ='normal')
                
                # Clear whatever's in the textBoxCollectionDatasetPIDs textbox
                textBoxCollectionDatasetPIDs.delete('1.0', END)

                # Insert the dataset PIDs into the textBoxCollectionDatasetPIDs scrollbox
                for dfIndex, dfRow in datasetInfoDF.iterrows():
                    datasetPid = dfRow['dataset_pid'] + '\n'
                    textBoxCollectionDatasetPIDs.insert('end', datasetPid)

            # Create and place result text with uniqueDatasetCount
            if deaccessionedDatasetCount == 0:
                text = f'Dataset versions found: {str(uniqueDatasetCount)}'
            if deaccessionedDatasetCount > 0:
                text = f'Dataset versions found: {str(uniqueDatasetCount)}\rDeaccessioned datasets ignored: {str(deaccessionedDatasetCount)}'

            if progressText is not None:
                progressText.set(text)
            else:
                print(text)

            return datasetInfoDF


def get_int_from_size_message(sizeEndpointJson):
    message = sizeEndpointJson['data']['message']

    if 'collection' in message:
        byteSizeString = message.lstrip('Total recorded size of the files stored in this collection (user-uploaded files plus the versions in the archival tab-delimited format when applicable): ').rstrip(' bytes')
        byteSizeInt = int(byteSizeString.replace(',', ''))

    elif 'dataset' in message:
        byteSizeString = message.lstrip('Total size of the files stored in this dataset: ').rstrip(' bytes')
        byteSizeInt = int(byteSizeString.replace(',', ''))

    return byteSizeInt


# Get byte size of files in dataset
def get_dataset_size(installationUrl, datasetIdOrPid, onlyPublishedFiles=False, apiKey=''):

    if onlyPublishedFiles == False:
        if apiKey=='':
            print('API key required to get sizes of all dataset versions')
            exit()

        if isinstance(datasetIdOrPid, str):
            datasetSizeEndpointUrl = f'{installationUrl}/api/datasets/:persistentId/storagesize?persistentId={datasetIdOrPid}'
        elif isinstance(datasetIdOrPid, int):
            datasetSizeEndpointUrl = f'{installationUrl}/api/datasets/{datasetIdOrPid}/storagesize'
        response = requests.get(
            datasetSizeEndpointUrl, headers={'X-Dataverse-key': apiKey})
        byteSizeTotalInt = get_int_from_size_message(sizeEndpointJson=response.json())

    elif onlyPublishedFiles == True:
        if isinstance(datasetIdOrPid, int):
            print('datasetIdOrPid must be a PID')
            exit()

        # Get metadata of all published versions
        allVersionMetadata = get_dataset_metadata_export(
            installationUrl, datasetPid=datasetIdOrPid, exportFormat='dataverse_json', 
            timeout=60, verify=False, excludeFiles=False, returnOwners=False,
            allVersions=True, headers={}, apiKey='')

        # Get sum of sizes of all unique files in all dataset versions
        byteSizeTotalInt = 0
        fileIdList = []

        for version in allVersionMetadata['data']:
            if len(version['files']) == 0:
                byteSizeInt = 0
            elif len(version['files']) > 0:
                for file in version['files']:
                    fileId = file['dataFile']['id']
                    if fileId not in fileIdList:
                        fileIdList.append(fileId)
                        byteSizeInt = file['dataFile']['filesize']
                        originalFileSize = improved_get(file, 'dataFile.originalFileSize', 0)
                        byteSizeTotalInt = byteSizeTotalInt + byteSizeInt + originalFileSize
        
    byteSizeTotalPretty = format_size(byteSizeTotalInt)
    sizeFormats = {
        'byteSizeTotalInt': byteSizeTotalInt,
        'byteSizeTotalPretty': byteSizeTotalPretty
    }

    return sizeFormats

# Get byte size of files in collection
def get_collection_size(installationUrl, apiKey, collectionIdOrAlias, includeSubCollections=True):

    if includeSubCollections is True:
        collectionSizeEndpointUrl = f'{installationUrl}/api/dataverses/{collectionIdOrAlias}/storage/use'

        response = requests.get(
            collectionSizeEndpointUrl, headers={'X-Dataverse-key': apiKey})
        byteSizeInt = get_int_from_size_message(sizeEndpointJson=response.json())
        byteSizePretty = format_size(byteSizeInt)

    # If we don't want to include sizes of files in collection's subcollections...
    elif includeSubCollections is False:
        # Use Get Contents API endpoint to get a list of PIDs of datasets published in the given collection
        datasetPids = []
        dataverseGetContentsEndpoint = f'{installationUrl}/api/dataverses/{collectionIdOrAlias}/contents'
        response = requests.get(
            dataverseGetContentsEndpoint,
            headers={'X-Dataverse-key': apiKey})
        data = response.json()

        for content in data['data']:
            if content['type'] == 'dataset':
                datasetPid = get_canonical_pid(content['persistentUrl'])
                datasetPids.append(datasetPid)

        # Get the sum of byte sizes of all datasets in datasetPids list
        datasetsSizeSum = 0

        for datasetPid in datasetPids:
            datasetSizeInt = get_dataset_size(installationUrl, datasetIdOrPid=datasetPid, apiKey=apiKey)['byteSizeTotalInt']
            datasetsSizeSum = datasetsSizeSum + datasetSizeInt

        byteSizeInt = datasetsSizeSum
        byteSizePretty = format_size(byteSizeInt)

    # Create dictionary that includes byte size as an int and a human readable string, e.g. 4MB
    sizeFormats = {
        'byteSizeInt': byteSizeInt,
        'byteSizePretty': byteSizePretty
    }

    return sizeFormats


def get_dataset_metadata_export(
    installationUrl, datasetPid, exportFormat, 
    timeout, verify, excludeFiles, returnOwners,
    allVersions=False, headers={}, apiKey=''):

    installationUrl = installationUrl.rstrip('/')

    if apiKey:
        headers['X-Dataverse-key'] = apiKey

    params = {
        'excludeFiles': excludeFiles,
        'returnOwners': returnOwners,
        'includeDeaccessioned': True
    }

    if isinstance(datasetPid, int):
        dataGetLatestVersionUrl = f'{installationUrl}/api/datasets/{datasetPid}/versions/:latest'
        dataGetAllVersionsUrl = f'{installationUrl}/api/datasets/{datasetPid}/versions'

    elif isinstance(datasetPid, str):
        dataGetLatestVersionUrl = f'{installationUrl}/api/datasets/:persistentId/versions/:latest'
        dataGetAllVersionsUrl = f'{installationUrl}/api/datasets/:persistentId/versions'
        
        params['persistentId'] = datasetPid

    if exportFormat == 'dataverse_json':
        if allVersions is False:
            try:
                response = requests.get(
                    dataGetLatestVersionUrl,
                    params=params,
                    headers=headers, 
                    timeout=timeout, 
                    verify=verify)
                if response.status_code == 200 and 'metadataBlocks' in response.json()['data']:
                    data = response.json()
                else:
                    data = 'ERROR'
            except Exception:
                data = 'ERROR'

        elif allVersions is True:
            try:
                response = requests.get(
                    dataGetAllVersionsUrl,
                    params=params,
                    headers=headers,
                    timeout=timeout, 
                    verify=verify)

                if response.status_code == 200 and 'metadataBlocks' in response.json()['data'][0]:
                    data = response.json()
                else:
                    data = 'ERROR'
            except Exception:
                data = 'ERROR'

    # For getting metadata from other exports, which are available only for each dataset's latest published
    # versions (whereas Dataverse JSON export is available for all draft and published versions)
    if exportFormat != 'dataverse_json':
        allVersions = False
        datasetMetadataExportEndpoint = f'{installationUrl}/api/datasets/export'
        datasetMetadataExportEndpoint = datasetMetadataExportEndpoint.replace('//api', '/api')
        try:
            response = requests.get(
                datasetMetadataExportEndpoint,
                params={
                    'persistentId': datasetPid,
                    'exporter': exportFormat
                    },
                headers=headers,
                timeout=timeout, 
                verify=verify)

            if response.status_code == 200:
                
                if exportFormat in ('schema.org' , 'OAI_ORE'):
                    data = response.json()

                if exportFormat in ('ddi' , 'oai_ddi', 'dcterms', 'oai_dc', 'Datacite', 'oai_datacite'):
                    string = response.text
                    data = BeautifulSoup(string, 'xml').prettify()
            else:
                data = f'ERROR: {response.status_code}; {response.text}'
        except Exception as e:
            data = f'ERROR: {e}'

    if data != 'ERROR' and exportFormat == 'dataverse_json' and excludeFiles is True:
        if allVersions is False:
            fileMetadata = improved_get(data, 'data.files', False)
        elif allVersions is True:
            latestVersionMetadata = data['data'][0]
            fileMetadata = improved_get(latestVersionMetadata, 'files', False)

        if fileMetadata is not False:
            print(
                'Warning: Installation may not support "excludeFiles" paramter.'\
                'File metadata may be included.')

    return data

def save_dataset_export(
    directoryPath, downloadStatusFilePath, installationUrl, datasetPid, 
    exportFormat, timeout, verify, excludeFiles, allVersions=False, 
    headers={}, apiKey=''):

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    with open(downloadStatusFilePath, mode='a', newline='', encoding='utf-8') as downloadStatusFile:
        writer = csv.writer(
            downloadStatusFile, delimiter=',', quotechar='"', 
            quoting=csv.QUOTE_MINIMAL)

        if allVersions == False:
            latestVersionMetadata = get_dataset_metadata_export(
                installationUrl, datasetPid, exportFormat, 
                timeout, verify=verify, 
                excludeFiles=excludeFiles, allVersions=False, returnOwners=False,
                headers={}, apiKey=apiKey)

            if latestVersionMetadata == 'ERROR':
                # Add to CSV file that the dataset's metadata was not downloaded
                writer.writerow([datasetPid, False]) 

            elif latestVersionMetadata != 'ERROR':
                datasetPidInJson = latestVersionMetadata['data']['datasetPersistentId']
                persistentUrl = get_url_form_of_pid(datasetPidInJson, installationUrl)

                # Get version number of latest version
                versionState = latestVersionMetadata['data']['versionState']
                if versionState == 'DRAFT':
                    latestVersionNumber = 'DRAFT'
                elif versionState == 'RELEASED':
                    majorVersionNumber = latestVersionMetadata['data']['versionNumber']
                    minorVersionNumber = latestVersionMetadata['data']['versionMinorNumber']
                    latestVersionNumber = f'v{majorVersionNumber}.{minorVersionNumber}'

                datasetPidForFileName = datasetPidInJson.replace(':', '_').replace('/', '_')

                metadataFile = f'{datasetPidForFileName}_{latestVersionNumber}(latest_version).json'
                with open(os.path.join(directoryPath, metadataFile), mode='w') as f:
                    f.write(json.dumps(latestVersionMetadata, indent=4))

                # Add to CSV file that the dataset's metadata was not downloaded
                writer.writerow([datasetPidInJson, True])

        elif allVersions == True:

            allVersionsMetadata = get_dataset_metadata_export(
                installationUrl, datasetPid, exportFormat, 
                timeout, verify, excludeFiles, returnOwners=False,
                allVersions=True, headers={}, apiKey=apiKey)

            if allVersionsMetadata == 'ERROR':
                # Add to CSV file that the dataset's metadata was not downloaded
                writer.writerow([datasetPid, False])

            elif allVersionsMetadata != 'ERROR':

                # Get the version number of the latest version
                latestMajorVersionNumber = allVersionsMetadata['data'][0]['versionNumber']
                latestMinorVersionNumber = allVersionsMetadata['data'][0]['versionMinorNumber']
                latestVersionNumber = f'v{latestMajorVersionNumber}.{latestMinorVersionNumber}'

                # Get the metadata of each dataset version
                for datasetVersion in allVersionsMetadata['data']:
                    datasetVersion = {
                        'status': 'OK',
                        'data': datasetVersion}

                    datasetPidInJson = datasetVersion['data']['datasetPersistentId']
                    persistentUrl = get_url_form_of_pid(datasetPidInJson, installationUrl)

                    versionState = datasetVersion['data']['versionState']
                    if versionState == 'DRAFT':
                        versionNumber = 'DRAFT'
                    elif versionState == 'RELEASED':
                        majorVersionNumber = datasetVersion['data']['versionNumber']
                        minorVersionNumber = datasetVersion['data']['versionMinorNumber']
                        versionNumber = f'v{majorVersionNumber}.{minorVersionNumber}'

                    datasetPidForFileName = datasetPidInJson.replace(':', '_').replace('/', '_')

                    if latestVersionNumber == versionNumber:
                        metadataFile = f'{datasetPidForFileName}_{versionNumber}(latest_version).json'
                    else:
                        metadataFile = f'{datasetPidForFileName}_{versionNumber}.json'

                    with open(os.path.join(directoryPath, metadataFile), mode='w') as f:
                        f.write(json.dumps(datasetVersion, indent=4))

                # Add to CSV file that the dataset's metadata was not downloaded
                writer.writerow([datasetPidInJson, True])  
        

def save_dataset_exports(directoryPath, downloadStatusFilePath, installationUrl, datasetPidList, 
    exportFormat, n_jobs, timeout, verify, excludeFiles, allVersions=False, headers={}, apiKey=''):
    
    currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')
    
    # Create CSV file and add headerrow
    headerRow = ['dataset_pid', 'dataverse_json_export_saved']
    with open(downloadStatusFilePath, mode='w', newline='') as downloadStatusFile:
        writer = csv.writer(downloadStatusFile)
        writer.writerow(headerRow)

    datasetCount = len(datasetPidList)

    # Use joblib library to use 4 CPU cores to make SearchAPI calls to get info about datasets
    # and report progress using tqdm progress bars
    with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=datasetCount)) as progress_bar:
        Parallel(n_jobs=n_jobs, backend='threading')(delayed(save_dataset_export)(
            directoryPath=directoryPath,
            downloadStatusFilePath=downloadStatusFilePath,
            installationUrl=installationUrl,
            datasetPid=datasetPid, 
            exportFormat=exportFormat,
            timeout=timeout,
            verify=verify,
            excludeFiles=excludeFiles,
            allVersions=allVersions, 
            headers={}, 
            apiKey=apiKey) for datasetPid in datasetPidList)
    

def get_metadatablock_data(installationUrl, metadatablockName):
    metadatablocksApiEndpoint = f'{installationUrl}/api/v1/metadatablocks/{metadatablockName}'

    response = requests.get(metadatablocksApiEndpoint)
    if response.status_code == 200:
        data = response.json()
        return data


def get_metadatablock_db_field_name_and_title(metadatablockData):
    # Get the database names of all fields
    allFieldsDBNamesList = []
    childFieldsDBNamesList = []

    for parentfield in metadatablockData['data']['fields']:
        properties = metadatablockData['data']['fields'][parentfield]
        field = properties['name']
        allFieldsDBNamesList.append(field)
        if 'childFields' in properties:
            for childField in properties['childFields']:
                childFieldsDBNamesList.append(childField)

    parentFieldsDBNamesList = list(set(allFieldsDBNamesList) - set(childFieldsDBNamesList))


    parentFieldDBNameAndTitleDict = {}
    for dbName in parentFieldsDBNamesList:
        dbNameProperties = metadatablockData['data']['fields'][dbName]
        parentFieldDBNameAndTitleDict[dbNameProperties['title']] = dbName

    return parentFieldDBNameAndTitleDict#, compoundFieldsDBNamesList


# Get list of parent field names and add to a tkinter listbox for user to choose fields
def get_parent_field_names(metadatablockData, listbox=None):
    

    if listbox is not None:
        # Clear any names already in the listbox
        listbox.delete(0, END)

    allFieldsDBNamesDict = {}
    childFieldsDBNamesList = []
    compoundFieldsDBNamesList = []

    for parentField in metadatablockData['data']['fields']:
        properties = metadatablockData['data']['fields'][parentField]
        field = properties['name']
        allFieldsDBNamesDict[field] = properties['title']

        if 'childFields' in properties:
            compoundFieldsDBNamesList.append(properties['title'])
            for childField in properties['childFields']:
                childFieldsDBNamesList.append(childField)

    options = []
    fieldWithChildFieldList = []
    for parentField in metadatablockData['data']['fields']:
        properties = metadatablockData['data']['fields'][parentField]
        if 'childFields' not in properties and properties['name'] not in childFieldsDBNamesList:
            fieldTitle = properties['title']
            options.append(' ' + fieldTitle)
        elif 'childFields' in properties:
            title = properties['title']
            childFieldDict = properties['childFields']
            childFieldsList = []
            for childField in childFieldDict:
                childFieldsList.append(childField)
            childFieldsString = list_to_string(childFieldsList)
            fieldWithChildField = f'{title}: {childFieldsString}'
            if len(fieldWithChildField) > 50:
                fieldWithChildField = fieldWithChildField[0:50] + '...'
            fieldWithChildFieldList.append(fieldWithChildField)
            options.append(' ' + fieldWithChildField)

    if listbox is not None:
        for option in options:
            listbox.insert('end', option)

    return(allFieldsDBNamesDict)

def get_listbox_values(listbox):
    selectedFields = []
    selections = listbox.curselection()
    for selection in selections:
        fieldName = listbox.get(selection).strip().split(':')[0]
        selectedFields.append(fieldName)
    return selectedFields


# Get the child field database names of compound fields or the database name of primitive fields
def get_column_names(metadatablockData, parentFieldTitle, parentFieldDBNameAndTitleDict):
    
    compoundFieldsDBNamesList = []
    for parentfield in metadatablockData['data']['fields']:
        properties = metadatablockData['data']['fields'][parentfield]
        if 'childFields' in properties:
            compoundFieldsDBNamesList.append(properties['name'])

    if parentFieldTitle in parentFieldDBNameAndTitleDict.keys():

        chosenDBName = parentFieldDBNameAndTitleDict[parentFieldTitle]
        columns = []

        # If the field is a compound field:
        if chosenDBName in compoundFieldsDBNamesList:

            # Get the child fields of the compound field
            dbNameProperties = metadatablockData['data']['fields'][chosenDBName]
            for field in dbNameProperties['childFields']:
                columns.append(field)

        # Other the field is a primitive field. Use its names as the column
        else:
            columns.append(chosenDBName)

        return columns


def get_metadata_values_lists(
    installationUrl, datasetMetadata, metadatablockName,
    chosenTitleDBName, chosenFields=None, versions='latestVersion'):

    # Get dictionary containing metadata block data
    if versions == 'allVersions':
        # versions = 'datasetVersion'
        metadatablockDict = datasetMetadata['data']['datasetVersion']['metadataBlocks']
    elif versions == 'latestVersion':
        metadatablockDict = datasetMetadata['data']['metadataBlocks']

    rowVariablesList = []

    if datasetMetadata['status'] == 'OK':
        
        # Get names of metadata blocks and name of first metadata block whose name matches the give metadatablockName
        matchingMetadataBlockName = None
        metadataBlockNamesList = []
        for metadatablock in metadatablockDict:
            metadataBlockNamesList.append(metadatablock)

        if metadatablockName in metadataBlockNamesList:
            matchingMetadataBlockName = metadatablockName

        elif metadatablockName not in metadataBlockNamesList:
            matchingMetadataBlockNames = [s for idx, s in enumerate(metadataBlockNamesList) if metadatablockName in s]
            if matchingMetadataBlockNames:
                matchingMetadataBlockName = matchingMetadataBlockNames[0]
            else:
                matchingMetadataBlockName is None

        if matchingMetadataBlockName is not None:

            # datasetPersistentUrl = datasetMetadata['data']['persistentUrl']
            datasetPid = datasetMetadata['data']['datasetPersistentId']
            datasetPersistentUrl = get_url_form_of_pid(datasetPid, installationUrl)
            datasetUrl = installationUrl + '/dataset.xhtml?persistentId=' + datasetPid

            versionCreateTime = datasetMetadata['data']['createTime']

            if 'publicationDate' not in datasetMetadata['data']:
                publicationDate = ''
            elif 'publicationDate' in datasetMetadata['data']:
                publicationDate = datasetMetadata['data']['publicationDate']

            if 'versionNumber' in datasetMetadata['data']:
                majorVersionNumber = datasetMetadata['data']['versionNumber']
                minorVersionNumber = datasetMetadata['data']['versionMinorNumber']
                datasetVersionNumber = f'{majorVersionNumber}.{minorVersionNumber}'
            else:
                datasetVersionNumber = 'DRAFT'

            for fields in metadatablockDict[matchingMetadataBlockName]['fields']:
                if fields['typeName'] == chosenTitleDBName:

                    # Save the field's typeClass and if it allows multiple values 
                    typeClass = fields['typeClass']
                    allowsMultiple = fields['multiple']

                    if typeClass in ('primitive', 'controlledVocabulary') and allowsMultiple is True:
                        for value in fields['value']:
                            rowVariables = [
                                datasetPid, datasetPersistentUrl, datasetUrl,
                                publicationDate, datasetVersionNumber, 
                                versionCreateTime,
                                value[:10000].replace('\r', ' - ')]
                            rowVariablesList.append(rowVariables)

                    elif typeClass in ('primitive', 'controlledVocabulary') and allowsMultiple is False:
                        value = fields['value'][:10000].replace('\r', ' - ')
                        rowVariables = [
                            datasetPid, datasetPersistentUrl, datasetUrl, 
                            publicationDate, datasetVersionNumber, 
                            versionCreateTime, value]

                        rowVariablesList.append(rowVariables)

                    elif typeClass == 'compound' and allowsMultiple is True:          
                        
                        index = 0
                        condition = True

                        while condition:
                            rowVariables = [
                                datasetPid, datasetPersistentUrl, datasetUrl, 
                                publicationDate, datasetVersionNumber,
                                versionCreateTime]

                            # Get number of multiples
                            total = len(fields['value'])

                            # For each child field...
                            for chosenField in chosenFields:
                                # Try getting the value of that child field
                                try:
                                    value = fields['value'][index][chosenField]['value']
                                    if isinstance(value, list):
                                        value = f'[{list_to_string(value)}]' 
                                    elif isinstance(value, str):
                                        value = value[:10000].replace('\r', ' - ')
                                # Otherwise, save an empty string as the value
                                except KeyError:
                                    value = ''
                                # Append value to the rowVariables list to add to the CSV file
                                rowVariables.append(value)

                            rowVariablesList.append(rowVariables)

                            index += 1
                            condition = index < total

                    elif typeClass == 'compound' and allowsMultiple is False:
                        rowVariables = [
                            datasetPid, datasetPersistentUrl, datasetUrl, 
                            publicationDate, datasetVersionNumber,
                            versionCreateTime]

                        for chosenField in chosenFields:
                            try:
                                value = fields['value'][chosenField]['value']
                                if isinstance(value, list):
                                    value = f'[{list_to_string(value)}]' 
                                elif isinstance(value, str):
                                    value = value[:10000].replace('\r', ' - ')
                                # Otherwise, save an empty string as the value
                            except KeyError:
                                value = ''
                            rowVariables.append(value)
                        rowVariablesList.append(rowVariables)

    return rowVariablesList


# Delete empty CSV files in a given directory.
# If file has fewer than 2 rows, delete it.
def delete_empty_csv_files(csvDirectory):
    fieldsWithNoMetadata = []
    for file in glob.glob(os.path.join(csvDirectory, '*.csv')):

        with open(file, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')
            data = list(reader)
            rowCount = len(data)
            if rowCount == 1:
                fieldName = Path(file).name.replace('.csv', '')
                fieldsWithNoMetadata.append(fieldName)
                f.close()
                os.remove(file)
    return fieldsWithNoMetadata


# Full outer join of CSV files in a given directory
def join_metadata_csv_files(csvDirectory):

    # Create CSV file in the directory that the user selected
    allMetadataFileName = os.path.join(csvDirectory, 'all_fields.csv')

    # Create list of common columns in CSV files to join on
    indexList = [
        'dataset_pid', 'dataset_pid_url', 'dataset_url', 'publication_date', 
        'dataset_version_number', 'dataset_version_create_time', 
        'dataverse_collection_alias']

    # Get list of CSV files in the csvDirectory
    filesList = listdir(csvDirectory)
    if len(filesList) > 1:
        filesDirectoryPathsList = []
        for file in filesList:
            fileDirectoryPath = os.path.join(csvDirectory, file)
            filesDirectoryPathsList.append(fileDirectoryPath)

        # Create a dataframe of each CSV file in the 'filesList' list
        dataframes = [pd.read_csv(table, sep=',', na_filter = False) for table in filesDirectoryPathsList]

        # For each dataframe, set the indexes (or the common columns across the dataframes to join on)
        for dataframe in dataframes:
            dataframe.set_index(indexList, inplace=True)

        # Full outer join all dataframes and save to the 'joined' variable
        joined = reduce(lambda left, right: left.join(right, how='outer', sort=False), dataframes)

        # Export joined dataframe to a CSV file
        joined.to_csv(allMetadataFileName, encoding='utf-8-sig')


# Get the metadata of datasets. Function passed to tkinter button
def get_dataset_metadata(
    rootWindow=None, progressLabel=None, progressText=None, noMetadataText=None, noMetadataLabel=None,
    installationUrl='', datasetPidString='', metadatablockName='citation',
    parentFieldTitleList='', directoryPath='', apiKey=''):

    # Use metadatablock API endpoint to get metadatablock data
    metadatablockData = get_metadatablock_data(installationUrl, metadatablockName)

    # From metadatablockData, get the database and display names of each parent field
    allFieldsDBNamesDict = get_metadatablock_db_field_name_and_title(metadatablockData)

    # Create directory in the directory that the user chose
    currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

    # Get name of repository
    req = requests.get(
        f'{installationUrl}/api/dataverses/1')
    data = req.json()
    installationName = data['data']['name'].replace(' ', '_').replace('__', '_')

    mainDirectoryName = f'{installationName}_dataset_metadata_{currentTime}'
    mainDirectoryPath = os.path.join(directoryPath, mainDirectoryName)
    os.mkdir(mainDirectoryPath)

    # For each field the user chose:
    for parentFieldTitle in parentFieldTitleList:

        # Create CSV file

        # Create file name and path
        csvFileName =  parentFieldTitle.lower().strip().replace(' ', '_')
        csvFileName = csvFileName + f'({metadatablockName})'
        mainDirectoryPath = os.path.join(directoryPath, mainDirectoryName)
        csvFilePath = os.path.join(mainDirectoryPath, csvFileName) + '.csv'
          
        # Create header row for the CSV file
        headerRow = [
            'dataset_pid', 'dataset_pid_url', 'dataset_url', 
            'publication_date', 'dataset_version_number', 
            'dataset_version_create_time', 'dataverse_collection_alias']

        childFieldsList = get_column_names(
            metadatablockData, parentFieldTitle, allFieldsDBNamesDict)
        # Add childFields list to header row
        headerRow = headerRow + childFieldsList

        # Create CSV file and add headerrow
        with open(csvFilePath, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headerRow)        

    # Change passed datasetPidString to a list by converting line breaks to commas, then using string_to_list function
    datasetPidString = datasetPidString.replace('\n', ',')
    datasetPidList = string_to_list(datasetPidString)
    datasetPidList = list(filter(None, datasetPidList))

    # Delete any message in the tkinter window about no metadata being found
    # the last time the "Get metadata" button was pressed
    if rootWindow is not None:
        noMetadataLabel.grid_forget()

    count = 0
    datasetTotalCount = len(datasetPidList)

    text = f'Dataset metadata retrieved: 0 of {datasetTotalCount}'
    if rootWindow is not None:
        progressText.set(text)
        progressLabel.grid(sticky='w', row=1, columnspan=2)
        rootWindow.update_idletasks()

    for datasetPid in datasetPidList:

        if rootWindow == None:
            print(f'{count} of {datasetTotalCount}: {datasetPid}')

        datasetPid = get_canonical_pid(datasetPid)

        # Get alias of collection that dataset is in
        searchApiUrl = f'{installationUrl}/api/search?q=dsPersistentId:"{datasetPid}"'
        requestsGetProperties = get_params(searchApiUrl)
        baseUrl = requestsGetProperties['baseUrl']
        params = requestsGetProperties['params']

        datasetInfoDF = get_object_dataframe_from_search_api(
            baseUrl=baseUrl, rootWindow=rootWindow, progressLabel=progressLabel, progressText=progressText,
            params=params, objectType='dataset', apiKey=apiKey)

        dataverseAlias = datasetInfoDF.iloc[0]['dataverse_collection_alias']

        # Get the JSON metadata export of the latest version of the dataset
        datasetMetadata = get_dataset_metadata_export(
            installationUrl=installationUrl,
            datasetPid=datasetPid, 
            exportFormat='dataverse_json',
            timeout=60,
            verify=False,
            excludeFiles=True,
            returnOwners=False,
            allVersions=False,
            apiKey=apiKey)

        if datasetMetadata['status'] == 'OK':

            for parentFieldTitle in parentFieldTitleList:
                # Get database name of parentFieldTitle
                dbName = allFieldsDBNamesDict[parentFieldTitle]

                valueLists = get_metadata_values_lists(
                    installationUrl=installationUrl,
                    datasetMetadata=datasetMetadata,
                    metadatablockName=metadatablockName,
                    chosenTitleDBName=dbName, 
                    chosenFields=get_column_names(
                        metadatablockData, parentFieldTitle, allFieldsDBNamesDict))                
                citationMetadataCsvFileName =  parentFieldTitle.lower().strip().replace(' ', '_')
                citationMetadataCsvFileName = citationMetadataCsvFileName + f'({metadatablockName})'
                citationMetadataCsvFilePath = os.path.join(mainDirectoryPath, citationMetadataCsvFileName) + '.csv'

                for valueList in valueLists:

                    # Insert alias of collection that dataset is published in
                    valueList.insert(6, dataverseAlias)

                    # Add row containing metadata of the dataset
                    with open(citationMetadataCsvFilePath, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        writer.writerow(valueList) 

        count += 1
        text = f'Dataset metadata retrieved: {count} of {datasetTotalCount}'
        if rootWindow is not None:
            progressText.set(text)
            progressLabel.grid(sticky='w', row=1, columnspan=2)
            rootWindow.update_idletasks()

    # Delete any CSV files in the mainDirectory that are empty and 
    # report in the app the deleted CSV files
    fieldsWithNoMetadata = delete_empty_csv_files(mainDirectoryPath)

    if count > 0 and len(fieldsWithNoMetadata) > 0:

        fieldsWithNoMetadataString = list_to_string(fieldsWithNoMetadata)
        fieldsWithNoMetadataString = (
            'No metadata found for the following fields:\r' + fieldsWithNoMetadataString)
        if rootWindow is not None:
            noMetadataText.set(fieldsWithNoMetadataString)
            noMetadataLabel.grid(sticky='w', row=2)
            rootWindow.update_idletasks()

    # Full outer join all CSV files to create a CSV with all metadata
    join_metadata_csv_files(mainDirectoryPath)


def delete_published_dataset(installationUrl, datasetPid, apiKey):
    destroyDatasetApiEndpointUrl = f'{installationUrl}/api/datasets/:persistentId/destroy/?persistentId={datasetPid}'
    req = requests.delete(
        destroyDatasetApiEndpointUrl,
        headers={'X-Dataverse-key': apiKey})
    data = req.json()

    status = data.get('status')
    print(status)

    if status:
        message = data.get('message', '')
        statusMessage = f'{status}: {message}'
        return statusMessage


def delete_published_datasets(
    rootWindow, progressLabel, progressText, notDeletedText, notDeletedLabel,
    installationUrl, datasetPidString, apiKey):

    installationStatusDict = check_installation_url_status(installationUrl)
    installationUrl = installationStatusDict['installationUrl']
    
    # Change passed datasetPidString to a list
    datasetPidList = [x.strip() for x in datasetPidString.splitlines()]

    # Remove any empty items from the list of dataset PIDs
    datasetPidList = [datasetPid for datasetPid in datasetPidList if datasetPid]

    canonicalPidList = []
    for datasetPid in datasetPidList:
        canonicalPid = get_canonical_pid(datasetPid)
        canonicalPidList.append(canonicalPid)

    # Delete any message in the tkinter window about datasets not being deleted
    # the last time the "Delete datasets" button was pressed
    notDeletedLabel.grid_forget()

    deletedDatasetCount = 0
    datasetTotalCount = len(canonicalPidList)

    deletedText = f'Datasets deleted: 0 of {datasetTotalCount}'
    progressText.set(deletedText)
    progressLabel.config(fg='green')
    progressLabel.grid(sticky='w', row=1)
    notDeletedLabel.config(fg='white')
    notDeletedLabel.grid(sticky='w', row=2)
    rootWindow.update_idletasks()

    destroyedDatasets = []
    notDestroyedDatasets = []

    for canonicalPid in canonicalPidList:
        
        statusMessage = delete_published_dataset(installationUrl, canonicalPid, apiKey)
        
        if 'OK' in statusMessage:
            destroyedDatasets.append(canonicalPid)
            deletedDatasetCount += 1
            deletedText = f'Datasets deleted: {deletedDatasetCount} of {datasetTotalCount}'
            progressText.set(deletedText)
            rootWindow.update_idletasks()

        elif 'ERROR' in statusMessage:
            notDeletedLabel.config(fg='red')
            notDestroyedDatasets.append(canonicalPid)
            notDestroyedDatasetsCount = len(notDestroyedDatasets)
            notDeletedMessage = f'Datasets not deleted: {notDestroyedDatasetsCount}'
            notDeletedText.set(notDeletedMessage)
            rootWindow.update_idletasks()

def save_locked_dataset_report(installationUrl='', directoryPath='', apiKey=''):
    # List lock types. See https://guides.dataverse.org/en/5.10/api/native-api.html?highlight=locks#list-locks-across-all-datasets
    lockTypesList = ['Ingest', 'finalizePublication']

    currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')
    currentTimeDateTime = convert_to_local_tz(datetime.now(), shortDate=False)

    lockedDatasetPids = []
    lockTypesString = list_to_string(lockTypesList)

    # Get dataset PIDs of datasets that have any of the lock types in lockTypesList
    for lockType in lockTypesList:
        datasetLocksApiEndpoint = f'{installationUrl}/api/datasets/locks?type={lockType}'
        response = requests.get(
            datasetLocksApiEndpoint,
            headers={'X-Dataverse-key': apiKey})
        data = response.json()

        if data['status'] == 'OK':
            for lock in data['data']:
                lockedDatasetPid = lock['dataset']
                lockedDatasetPids.append(lockedDatasetPid)

    # Use set function to deduplicate lockedDatasetPids list and convert set to a list again
    lockedDatasetPids = list(set(lockedDatasetPids))

    total = len(lockedDatasetPids)

    # Create CSV file and header row
    csvOutputFile = f'dataset_locked_status_{currentTime}.csv'
    csvOutputFilePath = os.path.join(directoryPath, csvOutputFile)

    with open(csvOutputFilePath, mode='w', newline='') as f:
        f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        f.writerow([
            'dataset_url', 'dataset_title', 'lock_reason', 'locked_date', 'time_locked', 'user_name',
            'contact_email', 'possible_duplicate_datasets', 'rt_ticket_urls'])

        if total == 0:
            datasetUrl = 'No locked datasets found'
            lockedDatasetTitle = reason = lockedDate = userName = ''
            contactEmailsString = potentialDuplicateDatasetsString = rtTicketUrlsString = ''

            f.writerow([
                datasetUrl, lockedDatasetTitle, reason, lockedDate, userName,
                contactEmailsString, potentialDuplicateDatasetsString])

        elif total > 0:

            lockedDatasetCount = 0

            # For each dataset, write to the CSV file info about each lock the dataset has
            for lockedDatasetPid in lockedDatasetPids:
                lockedDatasetCount += 1

                datasetMetadata = get_dataset_metadata_export(
                    installationUrl=installationUrl, datasetPid=lockedDatasetPid, 
                    exportFormat='dataverse_json', timeout=30,
                    verify=True, excludeFiles=True, returnOwners=False,
                    allVersions=False, apiKey=apiKey)

                # Get title of latest version of the dataset
                for field in datasetMetadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
                    if field['typeName'] == 'title':
                        lockedDatasetTitle = field['value']

                # Get contact email addresses of the dataset
                contactEmailsList = []

                for field in datasetMetadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
                    if field['typeName'] == 'datasetContact':
                        for contact in field['value']:
                            contactEmail = contact['datasetContactEmail']['value']
                            contactEmailsList.append(contactEmail)
                contactEmailsString = list_to_string(contactEmailsList)

                # # If RT username and password is provided, log into RT and use the contact email addresses to
                # # search for support emails from the dataset depositor
                # if rtUserLogin and rtUserPassword != '':
                #     import pkg_resources
                #     pkg_resources.require('rt==2.1.1')
                #     import rt
                #     # Log in to RT to search for support emails from the dataset depositors
                #     # print('\tLogging into RT support email system')
                #     tracker = rt.Rt('https://help.hmdc.harvard.edu/REST/1.0/', rtUserLogin, rtUserPassword)
                #     tracker.login()

                #     # print('\tSearching for related emails in the RT support email system')
                #     rtTicketUrlsList = []
                #     for contactEmail in contactEmailsList:

                #         # Search RT system for emails sent from the contact email address
                #         searchResults = tracker.search(
                #             Queue='dataverse_support', 
                #             raw_query=f'Requestor.EmailAddress="{contactEmail}"')

                #         # If there are any RT tickets found, save the ticket URL
                #         if len(searchResults) > 0:
                #             for rtTicket in searchResults:
                #                 rtTicketID = rtTicket['numerical_id']
                #                 rtTicketUrl = f'https://help.hmdc.harvard.edu/Ticket/Display.html?id={rtTicketID}'
                #                 rtTicketUrlsList.append(rtTicketUrl)

                #             # Use set function to deduplicate rtTicketUrlsList list and convert set to a list again
                #             rtTicketUrlsList = list(set(rtTicketUrlsList))

                #             # Convert list of ticket URLs to a string (to add to CSV file later)
                #             rtTicketUrlsString = list_to_string(rtTicketUrlsList)
                #         if len(searchResults) == 0:
                #             rtTicketUrlsString = 'No RT tickets found'

                # # If no RT username and password are provided...
                # elif rtUserLogin or rtUserPassword == '':
                #     rtTicketUrlsString = 'Not logged into RT. Provide RT username and password'

                # Get all data about locks on the dataset
                getAllLocksofDatasetApiEndpoint = f'{installationUrl}/api/datasets/:persistentId/locks?persistentId={lockedDatasetPid}'
                allLockData = requests.get(getAllLocksofDatasetApiEndpoint).json()

                for lock in allLockData['data']:
                    datasetUrl = f'{installationUrl}/dataset.xhtml?persistentId={lockedDatasetPid}&version=DRAFT'
                    reason = lock['lockType']
                    lockedDate = convert_to_local_tz(lock['date'])

                     # Get difference between current time and time of lock
                    timeLocked = get_duration(currentTimeDateTime - lockedDate)
                    
                    userName = lock['user']

                    # Use User Traces API endpoint to search for and return the DOIs of the depositor's datasets
                    # with titles that are similar to the locked dataset's title

                    userTracesApiEndpointUrl = f'{installationUrl}/api/users/{userName}/traces'

                    response = requests.get(
                        userTracesApiEndpointUrl,
                        headers={'X-Dataverse-key': apiKey})
                    userTracesData = response.json()

                    createdDatasetPidsList = []
                    potentialDuplicateDatasetsList = []

                    # If API endpoint fails, report failure in potentialDuplicateDatasetsString variable
                    if userTracesData['status'] == 'ERROR':
                        errorMessage = userTracesData['message']
                        potentialDuplicateDatasetsString = f'Unable to find depositor\'s datasets. User traces API endpoint failed: {errorMessage}'

                    # If API endpoint works but only one dataset is found, then that's the locked dataset
                    # and there are no duplicate datasets. Report that.
                    elif userTracesData['status'] == 'OK' and 'datasetCreator' in userTracesData['data']['traces'] and userTracesData['data']['traces']['datasetCreator']['count'] == 1:
                        potentialDuplicateDatasetsString = 'No duplicate datasets found'

                    # If API endpoint works and more than one dataset is found, then get the titles of
                    # those datasets, use fuzzywuzzy library to return any titles that are close to
                    # the title of the locked dataset
                    elif userTracesData['status'] == 'OK' and 'datasetCreator' in userTracesData['data']['traces'] and userTracesData['data']['traces']['datasetCreator']['count'] > 1:
                        for item in userTracesData['data']['traces']['datasetCreator']['items']:
                            createdDatasetPid = item['pid']
                            if createdDatasetPid != lockedDatasetPid:
                                createdDatasetPidsList.append(createdDatasetPid)

                        datasetTitles = []
                        
                        for createdDatasetPid in createdDatasetPidsList:
                            datasetMetadata = get_dataset_metadata_export(
                                installationUrl=installationUrl, datasetPid=createdDatasetPid, 
                                exportFormat='dataverse_json', timeout=30, verify=True,
                                excludeFiles=True, allVersions=False, returnOwners=False,
                                headers={}, apiKey=apiKey)

                            # Get title of latest version of the dataset
                            if 'latestVersion' in datasetMetadata['data']:
                                for field in datasetMetadata['data']['latestVersion']['metadataBlocks']['citation']['fields']:
                                    if field['typeName'] == 'title':
                                        datasetTitle = field['value']
                                        datasetTitles.append(datasetTitle)
                                        tokenSetScore = fuzz.token_set_ratio(lockedDatasetTitle, datasetTitle)
                                        if tokenSetScore >= 80:
                                            potentialDuplicateDatasetsList.append(createdDatasetPid)
                        if len(potentialDuplicateDatasetsList) == 0:
                            potentialDuplicateDatasetsString = 'No duplicate datasets found'
                        elif len(potentialDuplicateDatasetsList) > 0:
                            potentialDuplicateDatasetsString = list_to_string(potentialDuplicateDatasetsList)

                    # Write information to the CSV file
                    f.writerow([
                        datasetUrl, lockedDatasetTitle, reason, lockedDate, timeLocked, userName,
                        contactEmailsString, potentialDuplicateDatasetsString])


def unlock_dataset(installationUrl, datasetPid, apiKey):
    unlockDatasetApiEndpointUrl = f'{installationUrl}/api/datasets/:persistentId/locks?persistentId={datasetPid}'
    req = requests.delete(
        unlockDatasetApiEndpointUrl,
        headers={'X-Dataverse-key': apiKey})
    data = req.json()

    status = data.get('status')

    if status:
        message = data.get('message', '')
        statusMessage = f'{status}: {message}'
        return statusMessage


def unlock_datasets(
    rootWindow, progressLabel, progressText, notUnlockedText, notUnlockedLabel,
    installationUrl, datasetPidString, apiKey):
    
    installationStatusDict = check_installation_url_status(installationUrl)
    installationUrl = installationStatusDict['installationUrl']
    
    # Change passed datasetPidString to a list. Make sure the last newline doesn't mess up the list
    datasetPidList = [x.strip() for x in datasetPidString.splitlines()]

    # Remove any empty items from the list of dataset PIDs
    datasetPidList = [datasetPid for datasetPid in datasetPidList if datasetPid]

    canonicalPidList = []
    for datasetPid in datasetPidList:
        canonicalPid = get_canonical_pid(datasetPid)
        canonicalPidList.append(canonicalPid)

    # Delete any message in the tkinter window about datasets not being unlocked
    # the last time the "Unlock datasets" button was pressed
    notUnlockedLabel.grid_forget()

    unlockedDatasetCount = 0
    datasetTotalCount = len(canonicalPidList)

    unlockedText = f'Datasets unlocked: 0 of {datasetTotalCount}'
    progressText.set(unlockedText)
    progressLabel.config(fg='green')
    progressLabel.grid(sticky='w', row=1)
    notUnlockedLabel.config(fg='white')
    notUnlockedLabel.grid(sticky='w', row=2)
    rootWindow.update_idletasks()

    unlockedDatasets = []
    notUnlockedDatasets = []

    for canonicalPid in canonicalPidList:
        
        statusMessage = unlock_dataset(installationUrl, canonicalPid, apiKey)
        
        if 'OK' in statusMessage:
            unlockedDatasets.append(canonicalPid)
            unlockedDatasetCount += 1
            unlockedText = f'Datasets unlocked: {unlockedDatasetCount} of {datasetTotalCount}'
            progressText.set(unlockedText)
            rootWindow.update_idletasks()

        elif 'ERROR' in statusMessage:
            notUnlockedLabel.config(fg='red')
            notUnlockedDatasets.append(canonicalPid)
            notUnlockedMessage = f'Datasets not unlocked: {len(notUnlockedDatasets)}'
            notUnlockedText.set(notUnlockedMessage)
            rootWindow.update_idletasks()


def get_monthly_counts(installationUrl, objects, directoryPath):
    # Create CSV file and add headerrow
    fileName = f'monthly_{objects}_count.csv'
    csvFilePath = f'{directoryPath}/{fileName}'
    with open(csvFilePath, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'count'])

    monthlyCountsApiEndpoint = f'{installationUrl}/api/info/metrics/{objects}/monthly'

    with open(csvFilePath, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        with requests.Session() as s:
            download = s.get(monthlyCountsApiEndpoint)

            decodedContent = download.content.decode('utf-8')

            cr = csv.reader(decodedContent.splitlines(), delimiter=',')
            countList = list(cr)
            for row in countList[1:]:
                writer.writerow(row)


def get_citation_count(datasetPid):
    pidForDatacite = datasetPid.replace('doi:', '')
    dataciteEventsAPI = f'https://api.datacite.org/dois/{pidForDatacite}'
    try:
        response = requests.get(dataciteEventsAPI)
        citationCount = response.json()['data']['attributes']['citationCount']
    except Exception:
        try:
            citationCount = response.json()['errors'][0]['title']
        except Exception as e:
            citationCount = e
    return citationCount


def get_all_guestbooks(installationUrl, collectionAlias, apiKey):
    dataverseAliasList = get_all_subcollection_aliases(
        collectionUrl = f'{installationUrl}/dataverse/{collectionAlias}', 
        apiKey=apiKey)

    dataverseCount = len(dataverseAliasList)
    if dataverseCount == 1:
        print(f'Getting the guestbooks for {dataverseCount} collection')
    elif dataverseCount > 1:
        print(f'Getting the guestbooks for {dataverseCount} collections')

    # Hard code list of column names so that extra columns are added for potential 
    # custom questions and answers
    customQuestionAnswerColumns = []
    for column in range(20):
        customQuestion = 'Custom Question %s' %(column+1)
        customAnswer = 'Custom Answer %s' %(column+1)
        customQuestionAnswerColumns.append(customQuestion)
        customQuestionAnswerColumns.append(customAnswer)

    columnNames = [
        'Guestbook', 'Dataset', 'Dataset PID', 'Date', 'Type', 'File Name', 'File Id',
        'File PID', 'User Name', 'Email', 'Institution', 'Position']

    columnNames = columnNames + customQuestionAnswerColumns

    guestbookDFsList = []
    for dataverseAlias in dataverseAliasList:
        getGuestbooksApiEndpoint = f'{installationUrl}/api/dataverses/{dataverseAlias}/guestbookResponses'

        guestbook = requests.get(
            getGuestbooksApiEndpoint,
            headers={'X-Dataverse-key': apiKey}).content

        guestbookDF = pd.read_csv(io.StringIO(guestbook.decode('utf-8')), names=columnNames)

        # Remove first row from dataframe since the column names have been replaced with columnNames
        guestbookDF = guestbookDF.iloc[1: , :]

        if len(guestbookDF) > 0: 
            guestbookDFsList.append(guestbookDF)
            count = len(guestbookDF)
            print(f'\tGuestbook for {dataverseAlias} saved')
        elif len(guestbookDF) == 0:
            print(f'\tGuestbook for {dataverseAlias} empty and not saved')

    # Combine all guestbooks into one dataframe
    allGuestbooksDF = pd.concat(guestbookDFsList, ignore_index=True)

    # Remove empty Column Question columns from the allGuestbooksDF dataframe
    emptyColumns = [col for col in allGuestbooksDF.columns if allGuestbooksDF[col].isnull().all()]
    for column in emptyColumns:
        if 'Custom ' not in column:
            emptyColumns.remove(column)
    allGuestbooksDF.drop(emptyColumns, axis=1, inplace=True)

    print(f'\nAll guestbooks saved to dataframe')

    return allGuestbooksDF


def get_identifiers_from_oai_pmh_page(dictData, verb):
    identifierList = []

    if isinstance(dictData['OAI-PMH'][verb]['header'], dict):
        if '@status' not in dictData['OAI-PMH'][verb]['header']:
            identifierList.append(dictData['OAI-PMH'][verb]['header']['identifier'])

    elif isinstance(dictData['OAI-PMH'][verb]['header'], list):
        for record in dictData['OAI-PMH'][verb]['header']:
            if '@status' not in record:
                identifierList.append(record['identifier'])

    identifierList = list(set(identifierList))
    return identifierList


def get_oai_pmh_record_count(harvestUrl, verb, metadataFormat, harvestingSet):
    if harvestingSet is None:
        oaiUrl = f'{harvestUrl}?verb={verb}&metadataPrefix={metadataFormat}'
    elif harvestingSet is not None:
        oaiUrl = f'{harvestUrl}?verb={verb}&set={harvestingSet}&metadataPrefix={metadataFormat}'    

    response = requests.get(oaiUrl, verify=False)

    if response.status_code == 503:
        countOfRecordsInOAIFeed = 'NA - 503 Service Unavailable'

    elif response.status_code == 200:
        dictData = xmltodict.parse(response.content)

        if 'resumptionToken' not in dictData['OAI-PMH'][verb]:
            identifierList = get_identifiers_from_oai_pmh_page(dictData, verb)
            countOfRecordsInOAIFeed = len(identifierList)

        elif 'resumptionToken' in dictData['OAI-PMH'][verb]:
            identifierList = []
            pageCount = 1
            print(f'\tCounting records in page {pageCount}', end='\r', flush=True)

            identifierListinPage = get_identifiers_from_oai_pmh_page(dictData, verb)
            identifierList = identifierList + identifierListinPage

            resumptionToken = improved_get(dictData, f'OAI-PMH.{verb}.resumptionToken.#text')

            while resumptionToken is not None:
                pageCount += 1
                print(f'\tCounting records in page {pageCount}. Resumption token: {resumptionToken}', end='\r', flush=True)

                oaiUrlResume = f'{harvestUrl}?verb={verb}&resumptionToken={resumptionToken}'
                response = requests.get(oaiUrlResume, verify=False)
                dictData = xmltodict.parse(response.content)

                identifierListinPage = get_identifiers_from_oai_pmh_page(dictData, verb)
                identifierList = identifierList + identifierListinPage

                resumptionToken = improved_get(dictData, f'OAI-PMH.{verb}.resumptionToken.#text')

            countOfRecordsInOAIFeed = len(list(set(identifierList)))

    return countOfRecordsInOAIFeed


def get_dataverse_installations_metadata(mainInstallationsDirectoryPath, apiKeysFilePath, installationHostnamesList, nJobsForApiCalls, requestTimeout, headers):

    # Function for getting metadata and other information from known Dataverse installations.
    # Used for publishing the datasets in the collection at https://dataverse.harvard.edu/dataverse/dataverse-ux-research-dataverse

    def get_dataset_info_dict(start, headers, installationName, misindexedDatasetsCount, getCollectionInfo=True):
        searchApiUrl = f'{installationUrl}/api/search'
        try:
            perPage = 10

            params = {
                'q': '*',
                'fq': ['-metadataSource:"Harvested"'],
                'type': ['dataset'],
                'per_page': perPage,
                'start': start}

            response = requests.get(
                searchApiUrl,
                params=params,
                headers=headers,
                verify=False)

            searchApiUrlData = response.json()

            # For each dataset, write the dataset info to the CSV file
            for i in searchApiUrlData['data']['items']:

                datasetPids.append(i['global_id'])

                if getCollectionInfo == False:
                    newRow = {
                        'dataverse_installation_name': installationName,
                        'dataset_pid': i['global_id'],
                        'dataset_pid_url': i['url']}
                elif getCollectionInfo == True:
                    newRow = {
                        'dataverse_installation_name': installationName,
                        'dataset_pid': i['global_id'],
                        'dataset_pid_url': i['url'],
                        'dataverse_collection_alias': i.get('identifier_of_dataverse', 'NA'),
                        'dataverse_collection_name': i.get('name_of_dataverse', 'NA')}
                datasetInfoDict.append(dict(newRow))

        # Print error message if misindexed datasets break the Search API call, and try the next page.
        # See https://github.com/IQSS/dataverse/issues/4225

        except Exception as e:
            print(f'per_page=10 url broken when start is {start}')

            # This code hasn't been tested because I haven't encountered Search API results with misindexed objects
            # since rewriting this code to use the joblib library
            for i in range(10):
                try:
                    perPage = 1
                    params['start'] = start + i

                    response = requests.get(
                        searchApiUrl,
                        params=params,
                        headers=headers,
                        verify=False)

                    response = requests.get(searchApiUrl)
                    data = response.json()

                    # For each dataset, write the dataset info to the CSV file
                    for i in data['data']['items']:

                        datasetPids.append(i['global_id'])

                        newRow = {
                            'dataset_pid': i['global_id'],
                            'dataset_pid_url': i['url'],
                            'dataverse_collection_alias': i.get('identifier_of_dataverse', 'NA'),
                            'dataverse_collection_name': i.get('name_of_dataverse', 'NA')}
                        datasetInfoDict.append(dict(newRow))

                except Exception:
                    print(f'per_page=10 url broken when start is {start}')
                    misindexedDatasetsCount += 1


    def get_dataverse_collection_info_web_scraping(installationUrl, datasetPid, datasetPidCollectionAliasDict):
        pageUrl = f'{installationUrl}/dataset.xhtml?persistentId={datasetPid}'
        response = requests.get(pageUrl)
        soup = BeautifulSoup(response.text, 'html.parser')
        mydivs = soup.find_all('a', {'class': 'dataverseHeaderDataverseName'})
        dataverseHeaderDataverseName = str(mydivs[0])
        collectionAlias = dataverseHeaderDataverseName.replace('<a class="dataverseHeaderDataverseName" href="/dataverse/', '').split('" style="color:')[0]
        collectionName = mydivs[0].text

        newRow = {
            'dataset_pid': datasetPid,
            'dataverse_collection_alias': collectionAlias,
            'dataverse_collection_name': collectionName
        }
        datasetPidCollectionAliasDict.append(dict(newRow))

        return datasetPidCollectionAliasDict


    def check_export(file, filesListFromExports):
        with open(file, 'r') as f:
            datasetMetadata = f.read()
            datasetMetadata = json.loads(datasetMetadata)

        datasetPidInJson = datasetMetadata['data']['datasetPersistentId']
        filesListFromExports.append(datasetPidInJson)


    def check_exports(jsonDirectory, spreadsheetFilePath):
        filesListFromExports = []
        jsonFileCountTotal = len(glob.glob(os.path.join(jsonDirectory, '*(latest_version).json')))

        with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=jsonFileCountTotal)) as progress_bar:
            Parallel(n_jobs=4, backend='threading')(delayed(check_export)(
                file=file,
                filesListFromExports=filesListFromExports
                ) for file in glob.glob(os.path.join(jsonDirectory, '*(latest_version).json')))

        datasetsDF = pd.read_csv(spreadsheetFilePath)
        datasetPidList = datasetsDF['dataset_pid'].values.tolist()

        countOfPids = len(datasetPidList)
        countFromFiles = len(filesListFromExports)

        missingDatasets = list(set(datasetPidList) - set(filesListFromExports))

        return(missingDatasets)


    # Get directory that this Python script is in
    currrentWorkingDirectory = os.getcwd()

    # Save current time for folder and file timestamps
    currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

    # Create the main directory that will store a directory for each installation
    mainInstallationsDirectoryPath = Path(mainInstallationsDirectoryPath)
    allInstallationsMetadataDirectory = os.path.join(mainInstallationsDirectoryPath, f'all_installation_metadata_{currentTime}')

    os.mkdir(allInstallationsMetadataDirectory)
    installationsDirectory = os.path.join(allInstallationsMetadataDirectory, 'installations')

    os.mkdir(installationsDirectory)

    # Read CSV file containing apikeys into a dataframe and convert to list to compare each installation name
    apiKeysFilePath = Path(apiKeysFilePath)
    apiKeysDF = pd.read_csv(apiKeysFilePath).set_index('hostname')
    installationsRequiringApiKeyList = apiKeysDF.index.tolist()

    # Get JSON data that the Dataverse installations map uses
    print('Getting Dataverse installation data...')
    mapDataUrl = 'https://raw.githubusercontent.com/IQSS/dataverse-installations/main/data/data.json'
    response = requests.get(mapDataUrl, headers=headers)
    mapdata = response.json()
    installations = [x for x in mapdata['installations'] if x['hostname'] in installationHostnamesList]
    mapadata = []
    mapdata['installations'] = installations

    countOfInstallations = len(mapdata['installations'])

    # Create CSV file for reporting info about each installation
    headerRow = [
        'Installation_name',
        'Known_hostname',
        'Installation_URL',
        'Dataverse_software_version',
        'Dataverse_software_version_sanitized',
        'Able_to_get_metadata?',
        'Time_taken_to_download_metadata_(seconds)',
        'Time_taken_to_download_metadata',
        'API_token_used',
        'Count_of_datasets_metadata_retrieved',
        'Count_of_datasets_metadata_not_retrieved',
        'PIDs_of_dataset_metadata_not_retrieved',
        'Metadata_block_names']

    installationInfoFilePath = os.path.join(allInstallationsMetadataDirectory, f'dataverse_installations_summary_{currentTime}.csv')

    with open(installationInfoFilePath, mode='w', newline='', encoding='utf-8') as installationInfo:
        installationInfoWriter = csv.writer(
            installationInfo, delimiter=',', quotechar='"',
            quoting=csv.QUOTE_MINIMAL)
        installationInfoWriter.writerow(headerRow)

    installationProgressCount = 0

    for installation in mapdata['installations']:

        installationProgressCount += 1

        installationName = installation['name']
        hostname = installation['hostname']
        
        print(f'\nChecking {installationProgressCount} of {countOfInstallations} installations: {installationName}')

        installationStatusDict = check_installation_url_status(f'https://{hostname}', requestTimeout, headers=headers)
        installationUrl = installationStatusDict['installationUrl']
        installationUrlStatusCode = installationStatusDict['statusCode']

        print(f'Installation status for {hostname}: {installationUrlStatusCode}')

        if installationUrlStatusCode != 200:
            installationStatus = installationUrlStatusCode
            dataverseVersion = f'installation_unreachable: {installationUrlStatusCode}'
            dataverseVersionSanitized = f'installation_unreachable: {installationUrlStatusCode}'
            ableToGetMetadata = False
            timeDifferenceInSeconds = 0
            timeDifferencePretty = f'installation_unreachable: {installationUrlStatusCode}'
            apiTokenUsed = f'installation_unreachable: {installationUrlStatusCode}'
            countOfDatasetsMetadataRetrieved = f'installation_unreachable: {installationUrlStatusCode}'
            countOfDatasetsMetadataNotRetrieved = f'installation_unreachable: {installationUrlStatusCode}'
            pidsOfDatasetMetadataNotRetrieved = f'installation_unreachable: {installationUrlStatusCode}'
            metadatablockNames = f'installation_unreachable: {installationUrlStatusCode}'

        # If there's a good response from the installation, check if Search API works by searching for installation's non-harvested datasets
        if installationUrlStatusCode == 200:

            # Save time and date when script started downloading from the installation to append it to the installation's directory and files
            currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

             # Create directory for the installation
            installationNameTemp = installationName.replace(' ', '_').replace('|', '-')
            installationDirectory = f'{allInstallationsMetadataDirectory}/installations/{installationNameTemp}_{currentTime}'
            os.mkdir(installationDirectory)

            apiTokenUsed = False

            # If the installation is in the dataframe of API keys, add API key to header dictionary
            # to use installation's API endpoints, which require an API key
            if hostname in installationsRequiringApiKeyList:
                apiTokenUsed = True

                apiKeyDF = apiKeysDF[apiKeysDF.index == hostname]
                apiKey = apiKeyDF.iloc[0]['apikey']
                headers['X-Dataverse-key'] = apiKey

            # Otherwise remove any API key from the header dictionary
            else:
                headers.pop('X-Dataverse-key', None)

            # Use the "Get Version" endpoint to get installation's Dataverse version (or set version as 'NA')
            getInstallationVersionApiUrl = f'{installationUrl}/api/v1/info/version'
            getInstallationVersionApiUrl = getInstallationVersionApiUrl.replace('//api', '/api')
            getInstallationVersionApiStatus = check_api_endpoint(getInstallationVersionApiUrl, headers, verify=False, json_response_expected=True)

            if getInstallationVersionApiStatus == 'OK':
                response = requests.get(getInstallationVersionApiUrl, headers=headers, timeout=requestTimeout, verify=False)
                getInstallationVersionApiData = response.json()
                dataverseVersion = getInstallationVersionApiData['data']['version']
                dataverseVersion = str(dataverseVersion.lstrip('v'))
                dataverseVersionSanitized = sanitize_version(dataverseVersion)
            else:
                dataverseVersion = 'NA'
                dataverseVersionSanitized = 'NA'

            print(f'Dataverse version: {dataverseVersion}')

            # Check if Search API works for the installation
            searchApiCheckUrl = f'{installationUrl}/api/v1/search?q=*&fq=-metadataSource:"Harvested"&type=dataset&per_page=1&sort=date&order=desc'
            searchApiCheckUrl = searchApiCheckUrl.replace('//api', '/api')
            searchApiStatus = check_api_endpoint(searchApiCheckUrl, headers, verify=False, json_response_expected=True)

            # If Search API works, from Search API query results, get count of local (non-harvested) datasets
            if searchApiStatus == 'OK':
                response = requests.get(searchApiCheckUrl, headers=headers, timeout=requestTimeout, verify=False)
                searchApiData = response.json()
                datasetCount = searchApiData['data']['total_count']
            else:
                datasetCount = 'NA'
            print(f'Search API status: {searchApiStatus}')

            # Report if the installation has no published, non-harvested datasets
            if datasetCount == 0:
                print('\nInstallation has 0 published, non-harvested datasets')
                ableToGetMetadata = 'No datasets found'

            # If there are local published datasets, get the PID of a local dataset (used later to check endpoints for getting dataset metadata)
            # And check if the installation's Search API results include info about the dataset's Dataverse collection
            if datasetCount != 'NA' and datasetCount > 0:
                firstItem = searchApiData['data']['items'][0]
                testDatasetPid = firstItem['global_id']
                if 'identifier_of_dataverse' in firstItem:
                    searchAPIIncludesCollectionInfo = True
                else:
                    searchAPIIncludesCollectionInfo = False                
            else:
                testDatasetPid = 'NA'

            # Check if endpoint for getting installation's metadata block files works and if so save metadata block files
            # in a directory
            metadatablocksApiEndpointUrl = f'{installationUrl}/api/v1/metadatablocks'
            metadatablocksApiEndpointUrl = metadatablocksApiEndpointUrl.replace('//api', '/api')
            getMetadatablocksApiStatus = check_api_endpoint(metadatablocksApiEndpointUrl, headers, verify=False, json_response_expected=True)

            if getMetadatablocksApiStatus != 'OK':        
                metadatablockNames = 'Metadata block API endpoint failed'

            # If API endpoint for getting metadata block files works...
            elif getMetadatablocksApiStatus == 'OK':        

                # Create a directory for the installation's metadata block files
                metadatablockFileDirectoryPath = f'{installationDirectory}/metadatablocks_v{dataverseVersion}'
                os.mkdir(metadatablockFileDirectoryPath)

                # Download metadata block JSON files
                response = requests.get(metadatablocksApiEndpointUrl, headers=headers, timeout=requestTimeout, verify=False)
                metadatablockData = response.json()

                # Get list of the installation's metadata block names
                metadatablockNames = []
                for i in metadatablockData['data']:
                    metadatablockName = i['name']
                    metadatablockNames.append(metadatablockName)

                print('\nDownloading metadata block JSON files into metadata blocks folder')

                for metadatablockName in metadatablockNames:
                    metadatablockApiEndpointUrl = f'{metadatablocksApiEndpointUrl}/{metadatablockName}'
                    response = requests.get(metadatablockApiEndpointUrl, headers=headers, timeout=requestTimeout, verify=False)
                    metadata = response.json()

                    # If the metadata block has fields, download the metadata block data into a JSON file
                    if len(metadata['data']['fields']) > 0:
                        metadatablockFile = os.path.join(metadatablockFileDirectoryPath, f'{metadatablockName}_v{dataverseVersion}.json')
                        with open(metadatablockFile, mode='w') as f:
                            f.write(json.dumps(response.json(), indent=4))

            # If a local dataset PID can be retreived, check if "Get dataset JSON" metadata export endpoints works
            if testDatasetPid != 'NA':
                getJsonApiUrl = f'{installationUrl}/api/v1/datasets/:persistentId/?persistentId={testDatasetPid}'
                getJsonApiUrl = getJsonApiUrl.replace('//api', '/api')
                getDataverseJsonApiStatus = check_api_endpoint(getJsonApiUrl, headers, verify=False, json_response_expected=True)

            else:
                getDataverseJsonApiStatus = 'NA'
                ableToGetMetadata = False
                timeDifferenceInSeconds = 0
                timeDifferencePretty = '0 seconds'
                countOfDatasetsMetadataRetrieved = 0
                countOfDatasetsMetadataNotRetrieved = 0
                pidsOfDatasetMetadataNotRetrieved = ''
                # metadatablockNames = 'Didn\'t try retrieving since \'Get Dataverse JSON endpoint wasn\'t used or failed\''
            print(f'"Get dataset JSON" API status: {getDataverseJsonApiStatus}')

            # If the "Get dataset JSON" endpoint was used and works, download the installation's metadatablock JSON files, dataset PIDs, and dataset metadata
            if getDataverseJsonApiStatus != 'OK':
                ableToGetMetadata = False
                timeDifferenceInSeconds = 0
                timeDifferencePretty = '0 seconds'
                countOfDatasetsMetadataRetrieved = 0
                countOfDatasetsMetadataNotRetrieved = 0
                pidsOfDatasetMetadataNotRetrieved = ''

            elif getDataverseJsonApiStatus == 'OK':
                ableToGetMetadata = True

                # Use the Search API to get the installation's dataset PIDs, try to get the name and alias of owning 
                # Dataverse Collection, and write them to a CSV file, and use the "Get dataset JSON" 
                # endpoint to get those datasets' metadata dataverse_JSON exports

                # Create start variables to paginate through SearchAPI results
                startInfo = get_search_api_start_list(datasetCount)
                startsListCount = startInfo['startsListCount']
                startsList = startInfo['startsList']

                print(f'\nSearching through {startsListCount} Search API page(s) to save info of {datasetCount} dataset(s) to CSV file:')

                misindexedDatasetsCount = 0
                datasetInfoDict = []
                datasetPids = []

                if searchAPIIncludesCollectionInfo == False:
                    getCollectionInfo = False
                else:
                    getCollectionInfo = True

                with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=startsListCount)) as progress_bar:
                    Parallel(n_jobs=1, backend='threading')(delayed(get_dataset_info_dict)(
                        start, headers, installationName, misindexedDatasetsCount, getCollectionInfo) for start in startsList)   

                # Get new dataset count based on number of PIDs saved from Search API
                datasetCount = len(datasetPids)

                # If there's a difference, print unique count and explain how this might've happened
                datasetPids = list(set(datasetPids))
                if len(datasetPids) != datasetCount:
                    print(f'Unique dataset PIDs found: {len(datasetPids)}. The installation\'s Search API is listing datasets more than once')

                if misindexedDatasetsCount > 0:
                    # Print count of unretrievable dataset PIDs due to misindexing
                    print(f'\n\nUnretrievable dataset PIDs due to misindexing: {misindexedDatasetsCount}\n')

                # Create dataframe from datasetInfoDict, which lists dataset basic info from Search API.
                # And remove duplicate rows from the dataframe. At least one repository has two published versions of the same dataset indexed. 
                # See https://dataverse.rhi.hi.is/dataverse/root/?q=1.00002
                datasetPidsFileDF = pd.DataFrame(datasetInfoDict).set_index('dataset_pid').drop_duplicates()

                # If Search API results don't include collection identifiers of each dataset,
                # scrape each dataset page to get them, then merge them with datasetPidsFileDF
                if searchAPIIncludesCollectionInfo == False:
                    print(f'\rCollection info not included in installation\'s Search API results. Scraping webpages to get collection aliases')
                    
                    datasetPidCollectionAliasDict = []
                    with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=datasetCount)) as progress_bar:
                        Parallel(n_jobs=nJobsForApiCalls, backend='threading')(delayed(get_dataverse_collection_info_web_scraping)(
                            installationUrl,
                            datasetPid,
                            datasetPidCollectionAliasDict
                            ) for datasetPid in datasetPids)

                    datasetPidCollectionAliasDF = pd.DataFrame(datasetPidCollectionAliasDict)
                    datasetPidsFileDF = pd.merge(datasetPidsFileDF, datasetPidCollectionAliasDF, how='left', on='dataset_pid')

                # Export datasetPidsFileDF as a CSV file...
                datasetPidsFile = f'{installationDirectory}/dataset_pids_{installationNameTemp}_{currentTime}.csv'
                datasetPidsFileDF.to_csv(datasetPidsFile, index=True)

                # Create directory for dataset JSON metadata
                dataverseJsonMetadataDirectory = f'{installationDirectory}/Dataverse_JSON_metadata_{currentTime}'
                os.mkdir(dataverseJsonMetadataDirectory)

                # For each dataset PID, download dataset's Dataverse JSON metadata export
                print('\nDownloading Dataverse JSON metadata to Dataverse_JSON_metadata folder:')

                # Create CSV file for recording if dataset metadata was downloaded
                downloadStatusFilePath = f'{installationDirectory}/download_status_{installationNameTemp}_{currentTime}.csv'
                headerRow = ['dataset_pid', 'dataverse_json_export_saved']
                with open(downloadStatusFilePath, mode='w', newline='', encoding='utf-8-sig') as downloadStatusFile:
                    writer = csv.writer(downloadStatusFile)
                    writer.writerow(headerRow)

                startJSONMetadataExportDownloadTime = convert_to_local_tz(datetime.now(), shortDate=False)

                save_dataset_exports(
                    directoryPath=dataverseJsonMetadataDirectory,
                    downloadStatusFilePath=downloadStatusFilePath,
                    installationUrl=installationUrl, 
                    datasetPidList=datasetPids, 
                    exportFormat='dataverse_json',
                    n_jobs=nJobsForApiCalls,
                    timeout=60,
                    verify=False,
                    excludeFiles=False, 
                    allVersions=True, 
                    headers=headers, 
                    apiKey='')

                # Create dataframe from downloadStatusFilePath
                downloadProgressDF = pd.read_csv(downloadStatusFilePath, sep=',', na_filter = False)

                # Get list and count of datasets whose metadata failed to download
                missingDatasetsDF = downloadProgressDF[downloadProgressDF.dataverse_json_export_saved == False]
                missingDatasetsList = missingDatasetsDF['dataset_pid'].values.tolist()
                missingDatasetsCount = len(missingDatasetsList)

                # Check JSON directory to make sure files actually exist for each dataset
                # Return list of datasets whose Dataverse JSON files are missing, if any
                print('\nChecking JSON directory for metadata export files of each dataset')
                datasetsMissingFromJSONDirectory = check_exports(dataverseJsonMetadataDirectory, downloadStatusFilePath)

                countOfDatasetsMetadataNotRetrieved = len(datasetsMissingFromJSONDirectory)
                pidsOfDatasetMetadataNotRetrieved = ''

                if len(datasetsMissingFromJSONDirectory) > 0:
                    print(f'\rFirst attempt to download all Dataverse JSON metadata exports failed. Trying a second time to download metadata of {len(datasetsMissingFromJSONDirectory)} datasets(s)')

                    pidsOfDatasetMetadataNotRetrieved = datasetsMissingFromJSONDirectory

                    # Try a second time to get these datasets' metadata exports

                    # Create CSV file for recording if dataset metadata was downloaded
                    downloadStatusSecondAttemptFilePath = f'{installationDirectory}/download_status_{installationNameTemp}_{currentTime}_2.csv'
                    headerRow = ['dataset_pid', 'dataverse_json_export_saved']
                    with open(downloadStatusSecondAttemptFilePath, mode='w', newline='', encoding='utf-8-sig') as downloadStatusFile:
                        writer = csv.writer(downloadStatusFile)
                        writer.writerow(headerRow)

                    save_dataset_exports(
                        directoryPath=dataverseJsonMetadataDirectory,
                        downloadStatusFilePath=downloadStatusSecondAttemptFilePath,
                        installationUrl=installationUrl, 
                        datasetPidList=pidsOfDatasetMetadataNotRetrieved, 
                        exportFormat='dataverse_json',
                        n_jobs=nJobsForApiCalls,
                        timeout=60,
                        verify=False,
                        excludeFiles=False, 
                        allVersions=True, 
                        headers=headers, 
                        apiKey='')

                    # Create dataframe from downloadStatusSecondAttemptFilePath
                    downloadProgressSecondAttemptDF = pd.read_csv(downloadStatusSecondAttemptFilePath, sep=',', na_filter = False)

                    # Get list and count of datasets whose metadata failed to download
                    missingDatasetsSecondAttemptDF = downloadProgressSecondAttemptDF[downloadProgressSecondAttemptDF.dataverse_json_export_saved == False]
                    missingDatasetsSecondAttemptList = missingDatasetsSecondAttemptDF['dataset_pid'].values.tolist()
                    missingDatasetsSecondAttemptCount = len(missingDatasetsSecondAttemptList)

                    if missingDatasetsSecondAttemptCount > 0:

                        print(f'\rUnable to get all metadata after second attempt. Dataset metadata missing: {missingDatasetsSecondAttemptCount}. Updating download status CSV file')

                        for datasetPid in missingDatasetsSecondAttemptList:
                            downloadProgressDF.loc[ downloadProgressDF['dataset_pid'] == datasetPid, 'dataverse_json_export_saved'] = False

                    os.remove(downloadStatusSecondAttemptFilePath)
                endJSONMetadataExportDownloadTime = convert_to_local_tz(datetime.now(), shortDate=False)

                timeDifferenceInSeconds = int((endJSONMetadataExportDownloadTime - startJSONMetadataExportDownloadTime).total_seconds())
                if timeDifferenceInSeconds < 1:
                    timeDifferenceInSeconds = 1
                timeDifferencePretty = get_duration(endJSONMetadataExportDownloadTime - startJSONMetadataExportDownloadTime)

                retrievedDatasetsDF = downloadProgressDF[downloadProgressDF.dataverse_json_export_saved == True]
                countOfDatasetsMetadataRetrieved = len(retrievedDatasetsDF)

                # Merge datasetPidsFileDF and downloadProgressDF
                mergedDF = pd.merge(datasetPidsFileDF, downloadProgressDF, how='left', on='dataset_pid')

                # Delete downloadProgress CSV file since its been merged with datasetPidsFile
                os.remove(downloadStatusFilePath)

                print('\nGetting categories of each Dataverse collection:')

                # Get and deduplicate list of collection aliases from datasetPidsFileDF, 
                # then use dataaverse collection api endpoint to create dataframe listing 
                # category of each dataverse. Then merge that dataframe with mergedDF
                aliasList = datasetPidsFileDF['dataverse_collection_alias'].values.tolist()
                aliasList = list(set(aliasList))

                dataverseCollectionInfoDict = []
                get_collections_info(installationUrl, aliasList, dataverseCollectionInfoDict, headers=headers, apiKey='')

                # Create dataframe from dictionary
                dataverseCollectionInfoDF = pd.DataFrame(dataverseCollectionInfoDict).drop_duplicates()

                # Retain only columns with aliases and categories
                dataverseCollectionInfoDF = dataverseCollectionInfoDF[['dataverse_collection_alias', 'dataverse_collection_type']]
                # dataverseCollectionInfoDF.to_csv(f'{installationDirectory}/dataverseCollectionInfoDF.csv', index=False)

                # Merge datasetPidsFileDF and downloadProgressDF
                mergedDF = pd.merge(mergedDF, dataverseCollectionInfoDF, how='left', on='dataverse_collection_alias').drop_duplicates()
                # mergedDF.drop_duplicates()

                # Force report's column order
                mergedDF = mergedDF[[
                    'dataverse_installation_name',
                    'dataset_pid',
                    'dataset_pid_url', 
                    'dataverse_collection_alias',
                    'dataverse_collection_name',
                    'dataverse_collection_type',
                    'dataverse_json_export_saved'
                    ]]

                # Export merged dataframe (overwriting old datasetPidsFile)
                mergedDF.to_csv(datasetPidsFile, index=False)

        with open(installationInfoFilePath, mode='a', newline='', encoding='utf-8-sig') as installationInfo:
            installationInfoWriter = csv.writer(
                installationInfo, delimiter=',',
                quotechar='"', quoting=csv.QUOTE_MINIMAL)
            installationInfoWriter.writerow([
                installationName, 
                hostname,
                installationUrl,
                dataverseVersion,
                dataverseVersionSanitized,
                ableToGetMetadata,
                timeDifferenceInSeconds,
                timeDifferencePretty,
                apiTokenUsed,
                countOfDatasetsMetadataRetrieved,
                countOfDatasetsMetadataNotRetrieved,
                pidsOfDatasetMetadataNotRetrieved,
                metadatablockNames])

        print('\n----------------------')


def edit_dataset_metadata_field(installationUrl, datasetPid, fieldValue, replace=False, apiKey=''):
    url = f'{installationUrl}/api/datasets/:persistentId/editMetadata'
    params = {
        'persistentId': datasetPid}
    if replace is True:
        params['replace'] = 'true'
    resp = requests.put(
        url,
        json=fieldValue,
        params=params,
        headers={
            'X-Dataverse-key': apiKey,
            'content-type': 'application/json'
        })
    resp.raise_for_status()


# Find and replace for field values in metadata blocks.
# Works only for simple fields that accept only one instance, e.g. title and notesText
def full_replace_metadata_field_value(installationUrl, apiKey, datasetPid, metadataBlockName, replaceField, fieldFromValue, fieldToValue):

    respData = get_dataset_metadata_export(
        installationUrl, datasetPid, exportFormat='dataverse_json', 
        timeout=120, verify=False,
        allVersions=False, headers={}, apiKey=apiKey)

    mdbFields = respData['data']['latestVersion']['metadataBlocks'][metadataBlockName]['fields']

    replaced = False

    for field in mdbFields:
        if field['typeName'] == replaceField and field['value'] == fieldFromValue:
            # countOfFieldInstancesFound += 1
            field['value'] = fieldToValue
            print(field)
            print(type(field))
            edit_dataset_metadata_field(installationUrl, datasetPid, field, replace=True)
            replaced = True

    return replaced


def get_dataverse_collection_categories(installationUrl, collectionAliasList, apiKey):
    collectionCategoriesDict = []

    loopObj = tqdm(bar_format=tqdm_bar_format, iterable=collectionAliasList)
    for collectionAlias in loopObj:
        loopObj.set_postfix_str(f'collection_alias: {collectionAlias}')

        collectionInfoEndpoint = f'{installationUrl}/api/dataverses/{collectionAlias}'
        headers = {'X-Dataverse-key': apiKey}
        response = requests.get(collectionInfoEndpoint, headers=headers)
        collectionInfoJson = response.json()

        newRow = {
            'dataverse_collection_alias': collectionAlias,
            'dataverse_collection_categories': collectionInfoJson['data']['dataverseType']
        }

        collectionCategoriesDict.append(dict(newRow))
        sleep(1)
    return collectionCategoriesDict


def update_dataverse_collection(installation, collectionAlias, metadata, apikey):
    # e.g. metadata = {"dataverseType": "JOURNALS"}
    # See dataverse-complete.json at https://guides.dataverse.org/en/6.4/api/native-api.html#create-a-dataverse-collection
    
    metadata = json.dumps(metadata)
    changeCollectionInfoEndpoint = f'{installationUrl}/api/dataverses/{collectionAlias}'

    response = requests.put(
        changeCollectionInfoEndpoint,
        headers={
            'X-Dataverse-key': apiKey,
            'content-type': 'application/json'},
        data=metadata)
    responseDict = response.json()
    print(responseDict)
    sleep(1)
