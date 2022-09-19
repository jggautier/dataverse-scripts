# Class for the getMetadataAsCSVsFrame frame

from dataverse_repository_curation_assistant_functions import *
import json
import os
import requests
import sys
import time
from tkinter import Tk, ttk, Frame, Label, StringVar, BooleanVar, font
from tkinter import Checkbutton, Listbox, MULTIPLE, filedialog, END, INSERT, N, E, S, W
from tkinter.scrolledtext import ScrolledText
from ttkthemes import ThemedTk
from tkinter.ttk import Entry, Progressbar, Combobox, OptionMenu, Scrollbar
try:
    from tkmacosx import Button
except ImportError:
    from tkinter import Button
import webbrowser

appPrimaryBlueColor = '#286090'
appPrimaryRedColor = '#BF0000'
appPrimaryGreenColor = '#218000'
appPrimaryGreyColor = '#6E6E6E'


class findAndUnlockDatasetsFrame(Frame):

    def __init__(self, theWindow, *args, **options):
        Frame.__init__(self, theWindow, *args, **options)

        self.ttkStyle = ttk.Style()
        self.root = Frame(self, bg='white')
        self.root.grid()        

        # Create collapsible panel for information about this task
        self.collapsibleTaskDescription = collapsiblePanel(
            self.root,
            text='What does this do?',
            default='closed', relief='raised', bg='white')
        self.collapsibleTaskDescription.grid(sticky='w', row=1, pady=5)

        self.frameTaskDescription = Frame(
            self.collapsibleTaskDescription.subFrame,
            bg='white', pady=10)

        textTaskDescription = (
            'Get information about datasets that are stuck in the publishing process and remove all locks '
            'from datasets you specify.'
            '\r\rInformation about datasets that have the "finalizePublication" or "Ingest" locks are added '
            'to a CSV file you can save and review. The CSV file includes each locked dataset\'s '
            'contact email address and the DOIs of any other datasets that might be duplicate datasets.')

        # Create labels for information about this task
        self.labelTaskDescription = Label(
            self.frameTaskDescription,
            text=textTaskDescription,
            wraplength=380, justify='left',
            bg='white', anchor='w')

        self.labelMoreInformationLink = Label(
            self.frameTaskDescription,
            text='For more information about dataset locks, see the API Guides page',
            wraplength=380, justify='left',
            fg='blue', bg='white', anchor='w',
            cursor='pointinghand')

        # Place frame and labels for information about this task
        self.frameTaskDescription.grid(sticky='w', row=0)
        self.labelTaskDescription.grid(sticky='w', row=0)
        self.labelMoreInformationLink.grid(sticky='w', row=1)
        self.labelMoreInformationLink.bind(
            '<Button-1>',
            lambda e: self.open_url('https://guides.dataverse.org/en/latest/api/native-api.html?highlight=locks#list-locks-across-all-datasets'))

        # Create collapsible panel for account credentials
        self.collapsibleAccountCredentials = collapsiblePanel(
            self.root,
            text='Account credentials',
            default='open', relief='raised', bg='white')
        self.collapsibleAccountCredentials.grid(sticky='w', row=2, pady=5)

        # Create and place frame for button and helptext for importing account credentials
        self.frameImportCredntials = Frame(
            self.collapsibleAccountCredentials.subFrame, 
            bg='white', pady=10)
        self.frameImportCredntials.grid(sticky='w', row=0)

        # Create button and helptext for importing account credentials
        self.buttonImportCredentials = Button(
            self.frameImportCredntials,
            text='Import credentials',
            bg=appPrimaryGreyColor, fg='white',
            command=lambda: import_credentials(
                    installationURLField=self.comboboxInstallationUrl,
                    apiKeyField=self.entryApiToken,
                    filePath=get_file_path(fileTypes=['yaml']), # function that asks user for directory
                    ))

        labelImportCredentialsHelpText = (
            'Select a YAML file from your computer to fill the Installation URL '
            'and API Token fields.')
        self.labelImportCredentials = Label(
            self.frameImportCredntials,
            text=labelImportCredentialsHelpText,
            anchor='w', wraplength=380, justify='left',
            bg='white', fg='grey')

        # Place button and help text for importing account credentials
        self.buttonImportCredentials.grid(sticky='w', column=0, row=0)
        self.labelImportCredentials.grid(sticky='w', column=0, row=1)  
        
        # Create and place frame for installation URL field label, textbox, and help text
        self.frameInstallationUrl = Frame(
            self.collapsibleAccountCredentials.subFrame, 
            bg='white', pady=10)
        self.frameInstallationUrl.grid(sticky='w', row=1)
        self.frameInstallationUrl.columnconfigure(0, weight=1)
        self.frameInstallationUrl.columnconfigure(1, weight=180)

        # Create field label, textbox and help text for installation URL field
        self.labelInstallationUrl = Label(
            self.frameInstallationUrl,
            text='Installation URL',
            anchor='w', bg='white')
        self.labelInstallationUrlAsterisk = Label(
            self.frameInstallationUrl,
            text='*', fg='red', justify='left',
            anchor='w', bg='white')

        installationsList = get_installation_list()
        currentVar = StringVar()
        self.comboboxInstallationUrl = Combobox(
            self.frameInstallationUrl, textvariable=currentVar, width=38)
        self.comboboxInstallationUrl['values'] = installationsList

        labelInstallationUrlHelpText = (
            'Select or type in the homepage of a Dataverse repository, '
            'e.g. https://demo.dataverse.org')
        self.labelInstallationUrlHelp = Label(
            self.frameInstallationUrl,
            text=labelInstallationUrlHelpText,
            anchor='w',
            wraplength=380, justify='left',
            bg='white', fg='grey')

        # Place field label, textbox and help text for installation URL field
        self.labelInstallationUrl.grid(sticky='w', column=0, row=0)
        self.labelInstallationUrlAsterisk.grid(sticky='w', column=1, row=0)        
        self.comboboxInstallationUrl.grid(sticky='w', column=0, row=1, columnspan=2)
        self.labelInstallationUrlHelp.grid(sticky='w', column=0, row=2, columnspan=2)
            
        # Create and place frame for API URL label, field and help text
        self.frameApiToken = Frame(
            self.collapsibleAccountCredentials.subFrame, 
            bg='white', pady=10)
        self.frameApiToken.grid(sticky='w', row=2)
        self.frameApiToken.columnconfigure(0, weight=1)
        self.frameApiToken.columnconfigure(1, weight=180)

        # Create field label, textbox and help text for API Token field
        self.labelApiToken = Label(
            self.frameApiToken,
            text='API Token',
            anchor='w', bg='white')
        self.labelApiTokenAsterisk = Label(
            self.frameApiToken,
            text='*', fg='red', justify='left',
            anchor='w', bg='white')

        self.entryApiToken = Entry(
            self.frameApiToken, width=40)

        labelApiTokenHelpText = (
            'A "super user" API Token of an installation administrator '
            'is required')
        self.labelApiTokenHelp = Label(
            self.frameApiToken,
            text=labelApiTokenHelpText,
            anchor='w', wraplength=380, justify='left',
            bg='white', fg='grey')

        # Place field label, textbox and help text for installation URL field
        self.labelApiToken.grid(sticky='w', column=0, row=0)
        self.labelApiTokenAsterisk.grid(sticky='w', column=1, row=0)
        self.entryApiToken.grid(sticky='w', row=1, columnspan=2)
        self.labelApiTokenHelp.grid(sticky='w', row=2, columnspan=2)


        ##############        

        # Create and place collapsible panel for getting locked datasets report
        self.collapsiblePanelLockedDatasetReport = collapsiblePanel(
            self.root,
            text='Save report',
            default='closed', relief='raised', bg='white')
        self.collapsiblePanelLockedDatasetReport.grid(sticky='w', row=3, pady=5)
        
        # Create and place frame for all "Locked dataset report" frames
        self.frameLockedDatasetsReport = Frame(self.collapsiblePanelLockedDatasetReport.subFrame, bg='white')
        self.frameLockedDatasetsReport.grid(row=1, pady=10)

        # Create button and helptext for getting locked datasets report
        self.buttonLockedDatasetsReport = Button(
            self.frameLockedDatasetsReport,
            text='Get locked datasets report',
            bg=appPrimaryGreyColor, fg='white',
            command=lambda: save_locked_dataset_report(
                    installationUrl=get_installation_url(self.comboboxInstallationUrl.get().strip()),
                    apiKey=self.entryApiToken.get().strip(),
                    # self.entryApiToken.get().strip()
                    directoryPath=get_directory_path()) # function that asks user for directory
            )

        labelframeLockedDatasetsReportHelpText = (
            'Save a CSV file that includes each locked dataset\'s '
            'URL, title, and contact email address; the type of lock, when it occured, and the username '
            'of the account that attempted to publish the dataset; and the DOIs of any other datasets that '
            'the depositor deposited with titles that are similar to the locked dataset, helpful for '
            'determining if the depositor has already published the same data in another dataset.')

        self.labelImportCredentials = Label(
            self.frameLockedDatasetsReport,
            text=labelframeLockedDatasetsReportHelpText,
            anchor='w', wraplength=380, justify='left',
            bg='white', fg='grey')

        # Place button and help text for importing account credentials
        self.buttonLockedDatasetsReport.grid(sticky='w', column=0, row=0)
        self.labelImportCredentials.grid(sticky='w', column=0, row=1)


        ##############

        # Create and place collapsible panel for entering datasets
        self.collapsiblePanelChooseDatasets = collapsiblePanel(
            self.root,
            text='Which datasets?',
            default='closed', relief='raised', bg='white')
        self.collapsiblePanelChooseDatasets.grid(sticky='w', row=4, pady=5)

        # Create Enter and place frame for field label, help text and text box for entering dataset PIDs or URLs
        self.frameEnterDatasets = Frame(self.collapsiblePanelChooseDatasets.subFrame, bg='white')
        self.frameEnterDatasets.grid(row=0, pady=10)

        self.frameSearchURLField = Frame(self.frameEnterDatasets, bg='white')
        self.frameSearchURLField.columnconfigure(0, weight=1)
        self.frameSearchURLField.columnconfigure(1, weight=180)

        self.frameAboutHelpText = Frame(self.frameEnterDatasets, bg='white')

        self.labelSearchURL = Label(
            self.frameSearchURLField,
            text='Enter dataset PIDs or URLs',
            bg='white', anchor='w')
        self.labelSearchURLAsterisk = Label(
            self.frameSearchURLField,
            text='*', fg='red', justify='left',
            anchor='w', bg='white')
        self.textBoxCollectionDatasetPIDs = ScrolledText(
            self.frameSearchURLField, 
            width=45, height=8)

        searchURLEntryHelpTextString = (
            'Enter each dataset URL or PID on a new line')
        
        self.labelSearchURLHelpText = Label(
            self.frameSearchURLField,
            text=searchURLEntryHelpTextString,
            fg='grey', bg='white', 
            wraplength=380, justify='left', anchor='w')

        # Place Enter Search URL field label, text box, and validation error label
        self.frameAboutHelpText.grid(sticky='w', row=0)
        self.frameSearchURLField.grid(sticky='w', row=1, pady=5)
        self.labelSearchURL.grid(sticky='w', column=0, row=1)
        self.labelSearchURLAsterisk.grid(sticky='w', column=1, row=1)
        self.textBoxCollectionDatasetPIDs.grid(sticky='w', row=2, columnspan=2)
        self.labelSearchURLHelpText.grid(sticky='w', row=3, columnspan=2)

        # Create Get Metadata frame, button and validation error message text
        self.framebuttonGetMetadata = Frame(self.root, bg='white')

        # When button is pressed, get the list of dataset PIDs from 
        # the get_datasets_from_search_url command that was run
        self.buttonGetMetadata = Button(
            self.framebuttonGetMetadata, 
            text='Unlock datasets', bg=appPrimaryGreenColor,
            fg='white', width=423, height=40,
            font=font.Font(size=15, weight='bold'),
            command=lambda: unlock_datasets(
                    rootWindow=self.framebuttonGetMetadata,
                    progressText=self.progressTextGetMetadata,
                    progressLabel=self.labelProgressTextGetMetadata,
                    notUnlockedText=self.fieldsWithNoMetadataText,
                    notUnlockedLabel=self.labelFieldsWithNoMetadata,
                    installationUrl=get_installation_url(self.comboboxInstallationUrl.get().strip()),
                    datasetPidString=self.textBoxCollectionDatasetPIDs.get('1.0', END),
                    # parentFieldTitleList=get_listbox_values(self.listboxSelectFieldNames),
                    # directoryPath=get_directory_path(), # function that asks user for directory
                    apiKey=self.entryApiToken.get().strip()
                    )
                )

        self.progressTextGetMetadata = StringVar()
        self.labelProgressTextGetMetadata = Label(
            self.framebuttonGetMetadata,
            textvariable=self.progressTextGetMetadata,
            fg='green', bg='white', anchor='w')

        self.fieldsWithNoMetadataText = StringVar()
        self.labelFieldsWithNoMetadata = Label(
            self.framebuttonGetMetadata,
            textvariable=self.fieldsWithNoMetadataText,
            anchor='w', wraplength=400, justify='left', fg='red', bg='white')

        # Place Get Metadata frame and button
        self.framebuttonGetMetadata.grid(sticky='w', row=6, pady=15)
        self.buttonGetMetadata.grid(sticky='w', column=0, row=0)
        self.labelFieldsWithNoMetadata.grid(sticky='w', row=1)

    def open_url(self, url):
        webbrowser.open_new(url)
