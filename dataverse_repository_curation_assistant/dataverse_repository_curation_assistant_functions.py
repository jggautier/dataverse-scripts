# Functions for the curation app
import contextlib
import csv
from datetime import datetime
from dateutil import tz
from dateutil.parser import parse
from functools import reduce
from fuzzywuzzy import fuzz, process
import json
import joblib
from joblib import Parallel, delayed
import glob
import os
from os import listdir
import math
import pandas as pd
from pathlib import Path
import re
import requests
import time
from tkinter import Tk, ttk, Frame, Label, IntVar, Checkbutton, filedialog, NORMAL, DISABLED
from tkinter import Listbox, MULTIPLE, StringVar, END, INSERT, N, E, S, W
from tkinter.ttk import Entry, Progressbar, OptionMenu, Combobox
from tqdm import tqdm
from urllib.parse import urlparse
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
        credsDict = yaml.safe_load(file)
        installationURL = credsDict['installationURL']
        apiKey = credsDict['apiToken']

    if forCurationApp is True:
        # Clear installationURLField and insert installationURL from YAML file
        installationURLField.set('')
        installationURLField.set(installationURL)

        # Clear apiKeyField and insert apiKey from YAML file
        apiKeyField.delete(0, END)
        apiKeyField.insert(END, apiKey)

    elif forCurationApp is False:
        return credsDict


def forget_widget(widget):
    exists = widget.winfo_exists()
    if exists == 1:
        widget.grid_forget()
    else:
        pass


# Function for getting value of nested key or returning nothing if nested key
# doesn't exist. If the value is a string, this truncates 
# the value to 10,000 characters, the character limit for many spreadsheet 
# applications, and removes carriage returns
def improved_get(_dict, path, default=None):
    for key in path.split('.'):
        try:
            _dict = _dict[key]
        except KeyError:
            return default
    if isinstance(_dict, int) or isinstance(_dict, dict):
        return _dict
    elif isinstance(_dict, str):
        return _dict[:10000].replace('\r', ' - ')


def list_to_string(lst): 
    string = ', '.join(lst)
    return string


def string_to_list(string):
    stringToList = list(string.split(','))
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
        timestamp = timestamp.strftime('%Y-%m-%d')

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


# Converts timedelta object that shows an amount of time as yy:mm:dd:hh:mm:ss,
# into more human readable string, e.g. 1 year, 8 months, 4 days...
def td_format(timeDeltaObject):
    seconds = int(timeDeltaObject.total_seconds())
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
            periodValue , seconds = divmod(seconds, periodSeconds)
            hasSeconds = 's' if periodValue > 1 else ''
            strings.append(f'{periodValue} {periodName}{hasSeconds}')

    return ', '.join(strings)


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


# Function for getting the server URL from a collection URL
# or what's entered in the Installatio URL field
def get_installation_url(string):
    if string.startswith('http'):
        parsed = urlparse(string)
        installationUrl = parsed.scheme + '://' + parsed.netloc
        return installationUrl
    elif '(' in string:
        installationUrl = re.search(r'\(.*\)', string).group()
        installationUrl = re.sub('\(|\)', '', installationUrl)
        return installationUrl


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


# Function for getting name of installation's root collection 
# (assumming root dataverse's ID is 1, which isn't the case with UVA Dataverse)
def get_root_alias_name(url):

    # If it's the UVA homepage URL, it's root alias is uva (whose database ID is not 1)
    if 'dataverse.lib.virginia.edu' in url:
        rootAlias = 'uva'

    # If's it's not the UVA homepage URL, get the alias of the collection whose database is 1
    elif '/dataverse/' in url:
        parsed = urlparse(url)
        url = parsed.scheme + '://' + parsed.netloc + '/api/dataverses/1'
        response = requests.get(url)
        dataverseData = response.json()
        rootAlias = dataverseData['data']['alias']
    elif '/dataverse/' not in url:
        url = f'{url}/api/dataverses/1'
        response = requests.get(url)
        dataverseData = response.json()
        rootAlias = dataverseData['data']['alias']

    return rootAlias


# Function for getting collection alias name of a given Dataverse Collection URL,
# including the "Root" collection
def get_alias_from_collection_url(url):

    # If /dataverse/ is not in the URL, assume it's the installation's server url...
    if '/dataverse/' not in url:
        # If it's the UVA homepage URL, get it's root alias, whose database ID is not 1
        if 'dataverse.lib.virginia.edu' in url:
            alias = 'uva'

        # If's it's not the UVA homepage URL, get the alias of the collection whose database is 1
        elif 'dataverse.lib.virginia.edu' not in url:
            installationUrl = get_installation_url(url)
            url = f'{installationUrl}/api/dataverses/1'
            response = requests.get(url)
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
def is_root_collection(url):
    if get_alias_from_collection_url(url) == get_root_alias_name(url):
        return True
    elif get_alias_from_collection_url(url) != get_root_alias_name(url):
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
def convert_common_html_encoding(string):
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

# Function that returns the params of a given Search API URL, to be used in requests calls
def get_params(apiSearchURL):
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
            paramValue = convert_common_html_encoding(paramValue)
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
            value = convert_common_html_encoding(value)
            value = value.replace('+', ' ')
            paramString = key + ':' + value
            fq.append(paramString)

    # If there are type param values in typeParamList, add as value to new "type" param
    if typeParamList:
        params['params']['type'] = typeParamList

    # If there are any fq params, add fq keys and values
    if len(fq) > 0:
        params['params']['fq'] = fq

    return params


# Gets info from Search API about a given dataverse, dataset or file
def get_value_row_from_search_api_object(item, installationUrl):
    if item['type'] == 'dataset':
        datasetUrl = installationUrl + '/dataset.xhtml?persistentId=' + item['global_id']
        dataverseUrl = installationUrl + '/dataverse/' + item['identifier_of_dataverse']
        fileCount = improved_get(item, '')
        newRow = {
            'dataset_pid': item['global_id'],
            'version_state': item['versionState'],
            'dataset_version_create_time': item['createdAt'],
            'file_count': item['fileCount'],
            'dataverse_collection_alias': item['identifier_of_dataverse'],
            'dataverse_name': item['name_of_dataverse']
            # 'dataverse_url': dataverseUrl
        }
    if item['type'] == 'dataverse':
        newRow = {
            'dataverse_database_id': item['entity_id'],
            'dataverse_collection_alias': item['identifier'],
            'dataverse_url': item['url'],
            'dataverse_name': item['name']
        }
    if item['type'] == 'file':
        if item.get('file_persistent_id'):
            filePersistentId = item['file_persistent_id']
        else:
            filePersistentId = ''
        newRow = {
            'file_database_id': item['file_id'],
            'file persistent_id': filePersistentId,
            'file_name': item['name'],
            'dataset_pid': item['dataset_persistent_id']
        }
    return newRow


def get_object_dictionary_from_search_api_page(installationUrl, header, params, start, objectInfoDict):
    searchApiUrl = f'{installationUrl}/api/search'
    params['start'] = start
    params['per_page'] = 10
    response = requests.get(
        searchApiUrl,
        params=params,
        headers=header
    )
    data = response.json()

    for item in data['data']['items']:
        newRow = get_value_row_from_search_api_object(item, installationUrl)
        objectInfoDict.append(dict(newRow))


# Uses Search API to return dataframe containing info about collectoins, datasets or files in an installation
# Write results to the tkinter window
def get_object_dataframe_from_search_api(
    url, params, objectType, printProgress=False,
    rootWindow=None, progressText=None, progressLabel=None, apiKey=None):

    installationUrl = get_installation_url(url)

    if apiKey:
        header = {'X-Dataverse-key': apiKey}
    else:
        header = {}

    params['type'] = objectType

    # Add param to show database IDs of each item
    params['show_entity_ids'] = 'true'

    # Get total count of objects
    params['per_page'] = 1

    response = requests.get(
        url,
        params=params,
        headers=header
    )

    # print(response.request.url)

    data = response.json()
    totalDatasetCount = data['data']['total_count']

    if None not in [rootWindow, progressText, progressLabel]:
        text = 'Looking for datasets...'
        progressText.set(text)
        progressLabel.config(fg='green')
        progressLabel = progressLabel.grid(sticky='w', row=0)
        rootWindow.update_idletasks()
    
    # Create start variables to paginate through SearchAPI results
    start = 0
    apiCallsCount = round(totalDatasetCount/10)
    startsList = [0]
    for apiCall in range(apiCallsCount):
        start = start + 10
        startsList.append(start)
    startsListCount = len(startsList)

    # misindexedObjectCount = 0
    objectInfoDict = []

    if None not in [rootWindow, progressText, progressLabel]:
        Parallel(
            n_jobs=4, 
            backend='threading')(delayed(get_object_dictionary_from_search_api_page)(
                installationUrl, header, params, start, objectInfoDict) for start in startsList)

    else:
        with tqdm_joblib(
            tqdm(
                bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', 
                total=startsListCount)) as progress_bar:
            Parallel(
                n_jobs=4, 
                backend='threading')(delayed(get_object_dictionary_from_search_api_page)(
                    installationUrl, header, params, start, objectInfoDict) for start in startsList)        

    objectInfoDF = pd.DataFrame(objectInfoDict)

    return objectInfoDF


# Uses "Get Contents" endpoint to return list of dataverse aliases of all subcollections in a given collection
def get_all_subcollection_aliases(collectionUrl, apiKey=''):

    parsed = urlparse(collectionUrl)
    installationUrl = parsed.scheme + '://' + parsed.netloc
    alias = parsed.path.split('/')[2]

    if apiKey:
        header = {'X-Dataverse-key': apiKey}
    else:
        header = {}

    # Get ID of given dataverse alias
    dataverseInfoEndpoint = f'{installationUrl}/api/dataverses/{alias}'

    response = requests.get(
        dataverseInfoEndpoint,
        headers=header)
    data = response.json()
    parentDataverseId = data['data']['id']

    # Create list and add ID of given dataverse
    dataverseIds = [parentDataverseId]

    # Get each subdataverse in the given dataverse
    for dataverseId in dataverseIds:
        dataverseGetContentsEndpoint = f'{installationUrl}/api/dataverses/{dataverseId}/contents'
        response = requests.get(
            dataverseGetContentsEndpoint,
            headers=header)
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
            headers=header)
        data = response.json()
        alias = data['data']['alias']
        dataverseAliases.append(alias)

    return dataverseAliases


def get_collection_info(installationUrl, alias, dataverseCollectionInfoDict, header={}, apiKey=''):

    try:
        viewCollectionApiEndpointURL = f'{installationUrl}/api/dataverses/{alias}'
        response = requests.get(
            viewCollectionApiEndpointURL,
            headers=header)
        data = response.json()

        if data['status'] == 'ERROR':
            creationDate = 'N/A'
            contactEmailsString = 'N/A'
            dataverseType = 'N/A'

        elif data['status'] == 'OK':
            creationDate = convert_to_local_tz(data['data']['creationDate'], shortDate=True)
            contactEmailsList = []
            for dataverseContact in data['data']['dataverseContacts']:
                contactEmail = dataverseContact['contactEmail']
                contactEmailsList.append(contactEmail)
            contactEmailsString = list_to_string(contactEmailsList)
            dataverseType = data['data']['dataverseType']

        newRow = {
            'dataverse_alias': alias,
            'dataverse_create_date': creationDate,
            'contact_emails': contactEmailsString,
            'dataverse_type': dataverseType
            }
        dataverseCollectionInfoDict.append(dict(newRow))

    except Exception as e:
        newRow = {
            'dataverse_alias': alias,
            'dataverse_create_date': 'N/A',
            'contact_emails': 'N/A',
            'dataverse_type': 'N/A'
            }
    dataverseCollectionInfoDict.append(dict(newRow))


def get_collections_info(installationUrl, aliasList, dataverseCollectionInfoDict, header, apiKey=''):
    aliasCount = len(aliasList)

    # Use joblib library to use 4 CPU cores to make SearchAPI calls to get info about datasets
    # and report progress using tqdm progress bars
    with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=aliasCount)) as progress_bar:
        Parallel(n_jobs=4, backend='threading')(delayed(get_collection_info)(
            installationUrl,
            alias,
            dataverseCollectionInfoDict,
            header,
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


def get_datasets_from_collection_or_search_url(
    url, rootWindow=None, progressLabel=None, progressText=None, textBoxCollectionDatasetPIDs=None, 
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
        url=baseUrl, rootWindow=rootWindow, progressLabel=progressLabel, progressText=progressText,
        params=params, objectType='dataset', apiKey=apiKey)
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
            if subdataverses == True and is_root_collection(url) == True:
                uniqueDatasetCount = len(datasetInfoDF)

            # If the user wants datasets in all subdataverses and the url
            # is not the root collection...
            elif subdataverses == True and is_root_collection(url) == False:
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
                alias = get_alias_from_collection_url(url)
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
            text = f'Datasets found: {str(uniqueDatasetCount)}'
        if deaccessionedDatasetCount > 0:
            text = f'Datasets found: {str(uniqueDatasetCount)}\rDeaccessioned datasets ignored: {str(deaccessionedDatasetCount)}'

        if progressText is not None:
            progressText.set(text)
        else:
            print(text)


def get_dataset_metadata_export(
    installationUrl, datasetPid, exportFormat, timeout, verify,
    allVersions=False, header={}, apiKey=''):
    if apiKey:
        header['X-Dataverse-key'] = apiKey

    if exportFormat == 'dataverse_json':
        if allVersions is False:
            dataGetLatestVersionUrl = f'{installationUrl}/api/datasets/:persistentId'
            dataGetLatestVersionUrl = dataGetLatestVersionUrl.replace('//api', '/api')
            try:
                response = requests.get(
                    dataGetLatestVersionUrl,
                    params={'persistentId': datasetPid},
                    headers=header, 
                    timeout=timeout, 
                    verify=verify)
                if response.status_code in (200, 401): # 401 is the unauthorized code. Valid API key is needed
                    data = response.json()
                else:
                    data = 'ERROR'
            except Exception:
                data = 'ERROR'

        elif allVersions is True:
            dataGetAllVersionsUrl = f'{installationUrl}/api/datasets/:persistentId/versions'
            dataGetAllVersionsUrl = dataGetAllVersionsUrl.replace('//api', '/api')
            try:
                response = requests.get(
                    dataGetAllVersionsUrl,
                    params={'persistentId': datasetPid},
                    headers=header,
                    timeout=timeout, 
                    verify=verify)
                if response.status_code in (200, 401): # 401 is the unauthorized code. Valid API key is needed
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
                headers=header,
                timeout=timeout, 
                verify=verify)

            if response.status_code == 200:
                
                if exportFormat in ('schema.org' , 'OAI_ORE'):
                    data = response.json()

                if exportFormat in ('ddi' , 'oai_ddi', 'dcterms', 'oai_dc', 'Datacite', 'oai_datacite'):
                    string = response.text
                    data = BeautifulSoup(string, 'xml').prettify()
            else:
                data = 'ERROR'
        except Exception:
            data = 'ERROR'

    return data

def save_dataset_export(
    directoryPath, downloadStatusFilePath, installationUrl, datasetPid, 
    exportFormat, timeout, verify, allVersions=False, header={}, apiKey=''):

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    with open(downloadStatusFilePath, mode='a', newline='', encoding='utf-8') as downloadStatusFile:
        writer = csv.writer(
            downloadStatusFile, delimiter=',', quotechar='"', 
            quoting=csv.QUOTE_MINIMAL)

        latestVersionMetadata = get_dataset_metadata_export(installationUrl, 
            datasetPid, exportFormat, timeout, verify=verify, allVersions=False, 
            header={}, apiKey=apiKey)
        
        if latestVersionMetadata == 'ERROR':
            # Add to CSV file that the dataset's metadata was not downloaded
            writer.writerow([datasetPid, False])  

        elif latestVersionMetadata != 'ERROR':
            persistentUrl = latestVersionMetadata['data']['persistentUrl']

            # Older Dataverse installations' JSON metadata exports don't include the datasetPersistentId key
            # So try to use the persistentUrl instead to get a canonical PID.
            datasetPidInJson = improved_get(latestVersionMetadata, 'data.latestVersion.datasetPersistentId')
            if datasetPidInJson is None:
                datasetPidInJson = get_canonical_pid(persistentUrl)   

            publisher = latestVersionMetadata['data']['publisher']
            publicationDate = improved_get(latestVersionMetadata, 'data.publicationDate')

            # Get version number of latest version
            versionState = latestVersionMetadata['data']['latestVersion']['versionState']

            if publicationDate == None:
                latestVersionNumber = 'UNPUBLISHED'
            elif versionState == 'DRAFT':
                latestVersionNumber = 'DRAFT'
            elif versionState == 'RELEASED':
                majorVersionNumber = latestVersionMetadata['data']['latestVersion']['versionNumber']
                minorVersionNumber = latestVersionMetadata['data']['latestVersion']['versionMinorNumber']
                latestVersionNumber = f'v{majorVersionNumber}.{minorVersionNumber}'

            if allVersions == False:
                datasetVersion = {
                    'status': latestVersionMetadata['status'],
                    'data': {
                        'persistentUrl': persistentUrl,
                        'publisher': publisher,
                        'publicationDate': publicationDate,
                        'datasetVersion': latestVersionMetadata['data']['latestVersion']}}

                datasetPidForFileName = datasetPidInJson.replace(':', '_').replace('/', '_')

                metadataFile = f'{datasetPidForFileName}_{latestVersionNumber}.json'
                with open(os.path.join(directoryPath, metadataFile), mode='w') as f:
                    f.write(json.dumps(datasetVersion, indent=4))

                # Add to CSV file that the dataset's metadata was not downloaded
                writer.writerow([datasetPidInJson, True])

            elif allVersions == True:

                allVersionsMetadata = get_dataset_metadata_export(installationUrl, 
                    datasetPid, exportFormat, timeout, verify=verify, allVersions=True, header={}, 
                    apiKey=apiKey)

                if allVersionsMetadata == 'ERROR':
                    # Add to CSV file that the dataset's metadata was not downloaded
                    writer.writerow([datasetPid, False])

                elif allVersionsMetadata != 'ERROR':

                    for datasetVersion in allVersionsMetadata['data']:
                        datasetVersion = {
                            'status': latestVersionMetadata['status'],
                            'data': {
                                'persistentUrl': persistentUrl,
                                'publisher': publisher,
                                'publicationDate': publicationDate,
                                'datasetVersion': datasetVersion}}

                        versionState = datasetVersion['data']['datasetVersion']['versionState']
                        if publicationDate == None:
                            versionNumber = 'UNPUBLISHED'
                        elif versionState == 'DRAFT':
                            versionNumber = 'DRAFT'
                        elif versionState == 'RELEASED':
                            majorVersionNumber = datasetVersion['data']['datasetVersion']['versionNumber']
                            minorVersionNumber = datasetVersion['data']['datasetVersion']['versionMinorNumber']
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
    exportFormat, timeout, verify, allVersions=False, header={}, apiKey=''):
    
    currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')
    
    # Create CSV file and add headerrow
    # downloadStatusFilePath = f'{installationDirectory}/download_progress_{installationName}_{currentTime}.csv'
    headerRow = ['dataset_pid', 'dataverse_json_export_saved']
    with open(downloadStatusFilePath, mode='w', newline='') as downloadStatusFile:
        writer = csv.writer(downloadStatusFile)
        writer.writerow(headerRow)

    datasetCount = len(datasetPidList)

    # Use joblib library to use 4 CPU cores to make SearchAPI calls to get info about datasets
    # and report progress using tqdm progress bars
    with tqdm_joblib(tqdm(bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}', total=datasetCount)) as progress_bar:
        Parallel(n_jobs=4, backend='threading')(delayed(save_dataset_export)(
            directoryPath=directoryPath,
            downloadStatusFilePath=downloadStatusFilePath,
            installationUrl=installationUrl,
            datasetPid=datasetPid, 
            exportFormat=exportFormat,
            timeout=timeout,
            verify=verify,
            allVersions=allVersions, 
            header={}, 
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
def get_parent_field_names(metadatablockData, listbox):
    
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

    for option in options:
        listbox.insert('end', option)


def get_listbox_values(listbox):
    selectedFields = []
    selections = listbox.curselection()
    for selection in selections:
        fieldName = listbox.get(selection).strip().split(':')[0]
        selectedFields.append(fieldName)
    return selectedFields


# Get the chiild field database names of compound fields or the database name of primitive fields
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

        # # Other the field is a primitive field. Use its names as the column
        else:
            columns.append(chosenDBName)

        return columns


def get_metadata_values_lists(
    installationUrl, datasetMetadata, metadatablockName,
    chosenTitleDBName, chosenFields=None, versions='latestVersion'):

    if versions == 'allVersions':
        versions = 'datasetVersion'
    rowVariablesList = []

    if (datasetMetadata['status'] == 'OK') and\
        (metadatablockName in datasetMetadata['data'][versions]['metadataBlocks']):

        datasetPersistentUrl = datasetMetadata['data']['persistentUrl']
        datasetPid = get_canonical_pid(datasetPersistentUrl)
        datasetUrl = installationUrl + '/dataset.xhtml?persistentId=' + datasetPid

        versionCreateTime = datasetMetadata['data'][versions]['createTime']

        if 'publicationDate' not in datasetMetadata['data']:
            publicationDate = ''
        elif 'publicationDate' in datasetMetadata['data']:
            publicationDate = datasetMetadata['data']['publicationDate']

        if 'versionNumber' in datasetMetadata['data'][versions]:
            majorVersionNumber = datasetMetadata['data'][versions]['versionNumber']
            minorVersionNumber = datasetMetadata['data'][versions]['versionMinorNumber']
            datasetVersionNumber = f'{majorVersionNumber}.{minorVersionNumber}'
        else:
            datasetVersionNumber = 'DRAFT'

        for fields in datasetMetadata['data'][versions]['metadataBlocks'][metadatablockName]['fields']:
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
                                value = fields['value'][index][chosenField]['value'][:10000].replace('\r', ' - ')
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
                            # Get value from compound field
                            value = fields['value'][chosenField]['value'][:10000].replace('\r', ' - ')
                        except KeyError:
                            value = ''
                        rowVariables.append(value)
                    rowVariablesList.append(rowVariables)

    return rowVariablesList


# Delete empty CSV files in a given directory.
# If file has fewer than 2 rows, delete it.
def delete_empty_csv_files(csvDirectory):
    fieldsWithNoMetadata = []
    for file in glob.glob(str(Path(csvDirectory)) + '/' + '*.csv'):
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
        joined = reduce(lambda left, right: left.join(right, how='outer'), dataframes)

        # Export joined dataframe to a CSV file
        joined.to_csv(allMetadataFileName, encoding='utf-8-sig')


# Get the metadata of datasets. Function passed to tkinter button
def get_dataset_metadata(
    rootWindow, progressLabel, progressText, noMetadataText, noMetadataLabel,
    installationUrl='', datasetPidString='', 
    parentFieldTitleList='', directoryPath='', apiKey=''):

    # Use metadatablock API endpoint to get metadatablock data
    metadatablockData = get_metadatablock_data(installationUrl, 'citation')

    # From metadatablockData, get the database and display names of each parent field
    allFieldsDBNamesDict = get_metadatablock_db_field_name_and_title(metadatablockData)

    # Create directory in the directory that the user chose
    currentTime = time.strftime('%Y.%m.%d_%H.%M.%S')

    # Get name of repository
    req = requests.get(
        f'{installationUrl}/api/dataverses/1')
    data = req.json()
    installationName = data['data']['name'].replace(' ', '_').replace('__', '_')

    # installationName = get_root_alias_name(installationUrl)


    mainDirectoryName = f'{installationName}_dataset_metadata_{currentTime}'
    mainDirectoryPath = str(Path(directoryPath + '/' + mainDirectoryName))
    os.mkdir(mainDirectoryPath)

    # For each field the user chose:
    for parentFieldTitle in parentFieldTitleList:

        # Create CSV file

        # Create file name and path
        csvFileName =  parentFieldTitle.lower().strip().replace(' ', '_')
        csvFileName = csvFileName + '(citation)'
        mainDirectoryPath = str(Path(directoryPath + '/' + mainDirectoryName))
        csvFilePath = str(Path(mainDirectoryPath, csvFileName)) + '.csv'
          
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

    # Change passed datasetPidString to a list. Make sure the last newline doesn't mess up the list
    datasetPidList = [x.strip() for x in datasetPidString.splitlines()][:-1]

    # Delete any message in the tkinter window about no metadata being found
    # the last time the "Get metadata" button was pressed
    noMetadataLabel.grid_forget()

    count = 0
    datasetTotalCount = len(datasetPidList)

    text = f'Dataset metadata retrieved: 0 of {datasetTotalCount}'
    progressText.set(text)
    progressLabel.grid(sticky='w', row=1, columnspan=2)
    rootWindow.update_idletasks()

    for datasetPid in datasetPidList:

        # Get alias of collection that dataset is in
        searchApiUrl = f'{installationUrl}/api/search?q=dsPersistentId:"{datasetPid}"'
        requestsGetProperties = get_params(searchApiUrl)
        baseUrl = requestsGetProperties['baseUrl']
        params = requestsGetProperties['params']

        datasetInfoDF = get_object_dataframe_from_search_api(
            url=baseUrl, rootWindow=rootWindow, progressLabel=None, progressText=None,
            params=params, objectType='dataset', apiKey=apiKey)

        dataverseAlias = datasetInfoDF.iloc[0]['dataverse_collection_alias']

        # Get the JSON metadata export of the latest version of the dataset
        datasetMetadata = get_dataset_metadata_export(
            installationUrl=installationUrl,
            datasetPid=datasetPid, 
            exportFormat='dataverse_json',
            verify=False,
            apiKey=apiKey)

        if datasetMetadata['status'] == 'OK':

            for parentFieldTitle in parentFieldTitleList:
                # Get database name of parentFieldTitle
                dbName = allFieldsDBNamesDict[parentFieldTitle]

                valueLists = get_metadata_values_lists(
                    installationUrl=installationUrl,
                    datasetMetadata=datasetMetadata,
                    metadatablockName='citation',
                    chosenTitleDBName=dbName, 
                    chosenFields=get_column_names(
                        metadatablockData, parentFieldTitle, allFieldsDBNamesDict))                
                citationMetadataCsvFileName =  parentFieldTitle.lower().strip().replace(' ', '_')
                citationMetadataCsvFileName = citationMetadataCsvFileName + '(citation)'
                citationMetadataCsvFilePath = str(Path(mainDirectoryPath, citationMetadataCsvFileName)) + '.csv'

                for valueList in valueLists:

                    # Insert alias of collection that dataset is published in
                    valueList.insert(6, dataverseAlias)

                    # Add row containing metadata of the dataset
                    with open(citationMetadataCsvFilePath, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        writer.writerow(valueList) 

        count += 1
        text = f'Dataset metadata retrieved: {count} of {datasetTotalCount}'
        progressText.set(text)
        rootWindow.update_idletasks()

    # Delete any CSV files in the mainDirectory that are empty and 
    # report in the app the deleted CSV files
    fieldsWithNoMetadata = delete_empty_csv_files(mainDirectoryPath)

    if count > 0 and len(fieldsWithNoMetadata) > 0:

        fieldsWithNoMetadataString = list_to_string(fieldsWithNoMetadata)
        fieldsWithNoMetadataString = (
            'No metadata found for the following fields:\r' + fieldsWithNoMetadataString)
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

    installationUrl = get_installation_url(installationUrl)
    
    # Change passed datasetPidString to a list. Make sure the last newline doesn't mess up the list
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
                    exportFormat='dataverse_json', apiKey=apiKey)

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
                    timeLocked = td_format(currentTimeDateTime - lockedDate)
                    
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
                                exportFormat='dataverse_json', header={}, apiKey=apiKey)

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
    
    installationUrl = get_installation_url(installationUrl)
    
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