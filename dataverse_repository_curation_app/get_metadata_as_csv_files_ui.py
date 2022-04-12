# App for getting the metadata of datasets as CSV files

from dataverse_repository_curation_app_functions import *
import json
import os
import requests
import sys
# import threading
import time
from tkinter import Tk, ttk, Frame, Label, IntVar, StringVar, BooleanVar, font
from tkinter import Checkbutton, Listbox, MULTIPLE, filedialog, END, INSERT, N, E, S, W
from tkinter.scrolledtext import ScrolledText
from ttkthemes import ThemedTk
from tkinter.ttk import Entry, Progressbar, Combobox, OptionMenu, Scrollbar
try:
    from tkmacosx import Button
except ImportError:
    from tkinter import Button
# import webbrowser


appPrimaryBlueColor = '#286090'
appPrimaryRedColor = '#BF0000'
appPrimaryGreyColor = '#6E6E6E'


class getMetadataAsCSVsFrame(Frame):

    def __init__(self, theWindow, *args, **options):
        Frame.__init__(self, theWindow, *args, **options)

        self.ttkStyle = ttk.Style()
        self.mainFrame = Frame(self, bg='white')
        self.mainFrame.grid()        

        # Create collapsible panel for information about this task
        self.collapsibleTaskDescription = collapsiblePanel(
            self.mainFrame,
            text='What does this do?',
            default='closed', relief='raised', bg='white')
        self.collapsibleTaskDescription.grid(sticky='w', row=1, pady=5)

        textTaskDescription = (
            'Get the "Citation" metadata of the latest version of each dataset '
            'in a Dataverse Collection or from a search query URL. '
            'Harvested datasets are always excluded and datasets may be excluded if they\'re '
            'linked in but not owned by the given Dataverse Collection.'
            '\r\rThis app will save one CSV file for each metadata field you choose and ' 
            'one CSV file that contains the metadata for all of the fields you choose.')

        # Create labels for information about this task
        self.labelTaskDescription = Label(
            self.collapsibleTaskDescription.subFrame,
            text=textTaskDescription,
            wraplength=380, justify='left',
            bg='white', anchor='w')

        # self.labelMoreInformationLink = Label(
        #     self.collapsibleTaskDescription.subFrame,
        #     text='See ... for more information.',
        #     justify='left',
        #     fg='blue', bg='white', anchor='w',
        #     cursor='pointinghand')

        # Place labels for information about this task
        self.labelTaskDescription.grid(sticky='w', row=0, pady=10)
        # self.labelMoreInformationLink.grid(sticky='w', row=1, pady=5)
        # self.labelMoreInformationLink.bind(
        #     '<Button-1>',
        #     lambda e: self.open_url('http://www.google.com'))

        # Create collapsible panel for account credentials
        self.collapsibleAccountCredentials = collapsiblePanel(
            self.mainFrame,
            text='Account credentials',
            default='open', relief='raised', bg='white')
        self.collapsibleAccountCredentials.grid(sticky='w', row=2, pady=5)

        # Create and place frame for installation URL field label, textbox, and help text
        self.frameInstallationUrl = Frame(
            self.collapsibleAccountCredentials.subFrame, 
            bg='white', pady=10)
        self.frameInstallationUrl.grid(sticky='w', row=0)
        self.frameInstallationUrl.columnconfigure(0, weight=1)
        self.frameInstallationUrl.columnconfigure(1, weight=180)

        # Create field label, textbox and help text for installation URL field
        self.labelInstallationUrl = Label(
            self.frameInstallationUrl,
            text='Installation URL',
            font='Helvetica', anchor='w', bg='white')
        self.labelInstallationUrlAsterisk = Label(
            self.frameInstallationUrl,
            text='*', fg='red', justify='left',
            font='Helvetica', anchor='w', bg='white')

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
            font='Helvetica', anchor='w',
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
        self.frameApiToken.grid(sticky='w', row=1)

        # Create field label, textbox and help text for API Token field
        self.labelApiToken = Label(
            self.frameApiToken,
            text='API Token',
            font='Helvetica', anchor='w', bg='white')
        self.entryApiToken = Entry(
            self.frameApiToken, width=40)
        labelApiTokenHelpText = (
            'The repository may require an API Token. You\'ll also need to '
            'enter an API Token to get the metadata of unpublished dataset '
            'versions that your account has permission to access')
        self.labelApiTokenHelp = Label(
            self.frameApiToken,
            text=labelApiTokenHelpText,
            font='Helvetica', anchor='w',
            wraplength=380, justify='left',
            bg='white', fg='grey')

        # Place field label, textbox and help text for installation URL field
        self.labelApiToken.grid(sticky='w', row=0)
        self.entryApiToken.grid(sticky='w', row=1)
        self.labelApiTokenHelp.grid(sticky='w', row=2)

        # Create and place collapsible panel for choosing datasets
        self.collapsiblePanelChooseDatasets = collapsiblePanel(
            self.mainFrame,
            text='Which datasets?',
            default='closed', relief='raised', bg='white')
        self.collapsiblePanelChooseDatasets.grid(sticky='w', row=3, pady=5)

        # Create and place frame for all "Choose dataset option frames
        self.frameChooseDatasets = Frame(self.collapsiblePanelChooseDatasets.subFrame, bg='white')
        self.frameChooseDatasets.grid(row=1)

        # Create Enter Dataverse collection URL frame, field label, 
        # text box, load datasets button, and scrolled textbox for PIDs
        self.frameCollectionURL = Frame(self.frameChooseDatasets, bg='white')
        self.frameCollectionURL.columnconfigure(0, weight=1)
        self.frameCollectionURL.columnconfigure(1, weight=180)

        self.labelCollectionURL = Label(
            self.frameCollectionURL,
            text='Dataverse Collection URL',
            font='Helvetica', anchor='w', bg='white')
        self.labelCollectionURLAsterisk = Label(
            self.frameCollectionURL,
            text='*', fg='red', justify='left',
            font='Helvetica', anchor='w', bg='white')
        self.entryCollectionURL = Entry(
            self.frameCollectionURL, width=40)
        # self.labelCollectionURLValidation = Label(
        #     self.frameCollectionURL,
        #     text='You must enter a Dataverse Collection URL',
        #     font='Helvetica', fg='red', bg='white', anchor='w')

        labelEntryCollectionURLHelpTextString = (
            'E.g. https://demo.dataverse.org/dataverse/name'
            '\r\rTo include all datasets in the repository, enter the repository\'s '
            'homepage URL, e.g. https://demo.dataverse.org, and click '
            '"Include datasets in all collections within this collection"')
        self.labelEntryCollectionURLHelpText = Label(
            self.frameCollectionURL,
            text=labelEntryCollectionURLHelpTextString,
            font='Helvetica', fg='grey', bg='white', 
            wraplength=380, justify='left', anchor='w')
        self.getSubdataverses = BooleanVar()
        self.checkboxGetSubdataverses = Checkbutton(
            self.frameCollectionURL,
            text="Include datasets in all collections within this collection", bg='white',
            variable=self.getSubdataverses, onvalue = True, offvalue = False)
        self.buttonLoadDatasets = Button(
            self.frameCollectionURL,
            text='Find datasets',
            # bg=appPrimaryBlueColor, fg='white',
            bg=appPrimaryGreyColor, fg='white',
            # width=140, height=30,
            command=lambda: get_datasets_from_collection_or_search_url(
                rootWindow=self.mainFrame,
                url=self.entryCollectionURL.get().strip(),
                progressLabel=self.labelLoadDatasetsProgressText,
                progressText=self.loadDatasetsProgressText,
                textBoxCollectionDatasetPIDs=self.textBoxCollectionDatasetPIDs,
                ignoreDeaccessionedDatasets=True,
                apiKey=self.entryApiToken.get().strip(),
                subdataverses=self.getSubdataverses.get()))
        
        # Place Enter Dataverse collection URL field label, text box, and validation error label 
        self.labelCollectionURL.grid(sticky='w', column=0, row=0)
        self.labelCollectionURLAsterisk.grid(sticky='w', column=1, row=0)
        self.entryCollectionURL.grid(sticky='w', row=1, columnspan=2)
        self.labelEntryCollectionURLHelpText.grid(sticky='w', row=2, columnspan=2)
        # self.labelCollectionURLValidation.grid(sticky='w', row=2)
        self.checkboxGetSubdataverses.grid(sticky='w', row=3, columnspan=2, pady=10)
        self.buttonLoadDatasets.grid(sticky='w', row=4, columnspan=2, pady=10)


        # Create Enter Search URL frames, field label, text box, and validation error label
        self.frameSearchURL = Frame(self.frameChooseDatasets, bg='white')

        self.frameSearchURLField = Frame(self.frameSearchURL, bg='white')
        self.frameSearchURLField.columnconfigure(0, weight=1)
        self.frameSearchURLField.columnconfigure(1, weight=180)

        self.frameAboutHelpText = Frame(self.frameSearchURL, bg='white')

        aboutSearchURLHelpTextString = (
            'Search for datasets in the repository, '
            'then copy the URL from your browser\'s address bar into Search URL')
        self.labelAboutSearchURLHelpText = Label(
            self.frameAboutHelpText,
            text=aboutSearchURLHelpTextString,
            font='Helvetica', fg='black', bg='white', 
            wraplength=385, justify='left', anchor='w')

        self.labelSearchURL = Label(
            self.frameSearchURLField,
            text='Search URL',
            font='Helvetica', bg='white', anchor='w')
        self.labelSearchURLAsterisk = Label(
            self.frameSearchURLField,
            text='*', fg='red', justify='left',
            font='Helvetica', anchor='w', bg='white')
        self.entrySearchURL = Entry(
            self.frameSearchURLField, width=40)

        searchURLEntryHelpTextString = (
            'E.g. https://demo.dataverse.org/dataverse/demo/?q=surveys')
            # '\r\rTo get a search URL, first search for datasets in the repository, '
            # 'then copy the URL from your browser\'s address bar')
        self.labelSearchURLHelpText = Label(
            self.frameSearchURLField,
            text=searchURLEntryHelpTextString,
            font='Helvetica', fg='grey', bg='white', 
            wraplength=380, justify='left', anchor='w')
        # self.labelSearchURLValidation = Label(
        #     self.frameSearchURLField,
        #     text='You must enter a search URL',
        #     font='Helvetica', fg='red', bg='white', anchor='w')
        self.buttonLoadDatasets = Button(
            self.frameSearchURLField,
            text='Find the datasets',
            bg=appPrimaryGreyColor, fg='white',
            width=140, height=30,
            command=lambda: get_datasets_from_collection_or_search_url(
                rootWindow=self.frameLoadDatasetsProgress,
                url=self.entrySearchURL.get().strip(),
                progressLabel=self.labelLoadDatasetsProgressText,
                progressText=self.loadDatasetsProgressText,
                textBoxCollectionDatasetPIDs=self.textBoxCollectionDatasetPIDs,
                apiKey=self.entryApiToken.get().strip(),
                ignoreDeaccessionedDatasets=True,
                subdataverses=self.getSubdataverses.get()))

        # Place Enter Search URL field label, text box, and validation error label
        self.frameAboutHelpText.grid(sticky='w', row=0)
        self.frameSearchURLField.grid(sticky='w', row=1, pady=5)
        self.labelAboutSearchURLHelpText.grid(sticky='w', row=0, pady=5)
        self.labelSearchURL.grid(sticky='w', column=0, row=1)
        self.labelSearchURLAsterisk.grid(sticky='w', column=1, row=1)
        self.entrySearchURL.grid(sticky='w', row=2, columnspan=2)
        self.labelSearchURLHelpText.grid(sticky='w', row=3, columnspan=2)
        # self.labelSearchURLValidation.grid(sticky='w', row=2)        
        self.buttonLoadDatasets.grid(sticky='w', row=4, columnspan=2, pady=15)

        # Create frame and labels for indicating progress and showing results
        self.frameLoadDatasetsProgress = Frame(self.frameChooseDatasets, bg='white')
        self.loadDatasetsProgressText = StringVar()
        self.labelLoadDatasetsProgressText = Label(
            self.frameLoadDatasetsProgress,
            textvariable=self.loadDatasetsProgressText,
            fg='green', bg='white', anchor='w', justify='left')
        self.textBoxCollectionDatasetPIDs = ScrolledText(
            self.frameLoadDatasetsProgress,
            width=45, height=5,
            font='Helvetica')

        # Place frame that holds widgets for indicating progress and showing results
        self.frameLoadDatasetsProgress.grid(sticky='w', row=4, pady=5)

        
        # # Create Enter dataset URLs or PIDs frame, field label,
        # # text box, and validation error label
        # self.frameEnterUrls = Frame(self.frameChooseDatasets, bg='white')
        # self.labelEnterDatasets = Label(
        #     self.frameEnterUrls,
        #     text='Enter dataset PIDs or URLs',
        #     font='Helvetica', bg='white', anchor='w')
        # self.textBoxEnterDatasets = ScrolledText(
        #     self.frameEnterUrls,
        #     width=45, height=10,
        #     font='Helvetica')
        # self.labelEnterDatasetsHelpText = Label(
        #     self.frameEnterUrls,
        #     text='Enter each URL or PID on a new line',
        #     font='Helvetica', bg='white', fg='grey', anchor='w')
        # self.labelEnterDatasetsValidation = Label(
        #     self.frameEnterUrls,
        #     text='You must enter at least one dataset URL or PID',
        #     font='Helvetica', fg='red', bg='white', anchor='w')
        # self.buttonLoadDatasets = Button(
        #     self.frameEnterUrls,
        #     text='Load datasets',
        #     bg=appPrimaryBlueColor, fg='white',
        #     width=110, height=30,
        #     command=lambda: get_datasets_from_pids_or_urls(
        #         installationUrl=self.entryInstallationUrl.get().strip(),
        #         # textBoxEnterDatasets = self.textBoxEnterDatasets,
        #         textBoxEnterDatasets = self.textBoxEnterDatasets.get('1.0','end-1c'),
        #         apiKey=self.entryApiToken.get().strip()))

        # # Place Enter dataset URLs or PIDs field label, text box, and validation error label
        # self.labelEnterDatasets.grid(sticky='w', row=0)
        # self.textBoxEnterDatasets.grid(sticky='w', row=1)
        # self.labelEnterDatasetsHelpText.grid(sticky='w', row=2)
        # self.labelEnterDatasetsValidation.grid(sticky='w', row=3)
        # self.buttonLoadDatasets.grid(sticky='w', row=4, pady=10)

        # # Create From list of dataset PIDs frame and browse button
        # self.frameDatasetList = Frame(self.frameChooseDatasets, bg='white')
        # self.buttonBrowseDatasetList = Button(
        #     self.frameDatasetList, 
        #     text='Browse', 
        #     bg=appPrimaryGreyColor, fg='white', 
        #     width=100, height=30,
        #     command=lambda: self.retrieve_csv_directory())
        # self.csvDirectory = '/Users/juliangautier/Desktop'
        # self.labelBrowseDatasetListConfirmation = Label(
        #     self.frameDatasetList,
        #     text='You chose: ' + self.csvDirectory, anchor='w',
        #     fg='green', bg='white', wraplength=380, justify='left')

        # # Place From list of dataset PIDs browse button
        # self.buttonBrowseDatasetList.grid(sticky='w', row=0)
        # self.labelBrowseDatasetListConfirmation.grid(sticky='w', row=1)
        
        # # Create Use local Dataverse JSON metadata files frame, field label, button, and validation error label 
        # self.frameBrowseJSONFiles = Frame(self.frameChooseDatasets, bg='white')
        # self.buttonBrowseJSONFiles = Button(
        #     self.frameBrowseJSONFiles, 
        #     text='Browse', 
        #     bg=appPrimaryGreyColor, fg='white', 
        #     width=100, height=30,
        #     command=lambda: self.retrieve_csv_directory())

        # self.jsonDirectory = '/Users/juliangautier/Desktop'
        # self.labelBrowseJSONFilesConfirmation = Label(
        #     self.frameBrowseJSONFiles,
        #     text='You chose: ' + self.jsonDirectory, anchor='w',
        #     fg='green', bg='white', wraplength=380, justify='left')

        # # Place Use local Dataverse JSON metadata files field label, button, and validation error label 
        # self.buttonBrowseJSONFiles.grid(sticky='w', row=0)
        # self.labelBrowseJSONFilesConfirmation.grid(sticky='w', row=1)

        # Create Select datasets label and dropdown for menu
        self.options = [
            'In a Dataverse Collection',
            'From a Search URL']
            # 'From dataset URLs or PIDs']
            # 'From a list of dataset PIDs',
            # 'From Dataverse JSON export files']
        self.dropdownOptionSelected = StringVar()
        self.dropdownOptionSelected.trace('w', self.get_datasets_method)
        self.dropdownMenuChooseDatasets = OptionMenu(
            self.collapsiblePanelChooseDatasets.subFrame,
            self.dropdownOptionSelected,
            self.options[0], *self.options)

        self.ttkStyle.configure('TMenubutton', foreground='black')
        # self.dropdownMenuChooseDatasets.entryconfigure(index, background='red')

        # Place dropdown for menu
        self.dropdownMenuChooseDatasets.grid(sticky='w', row=0, pady=10)

        # Create and place collapsible panel for entering metadata field database names
        self.collapsiblePanelWhichFields = collapsiblePanel(
            self.mainFrame,
            text='Which metadata fields?',
            default='closed', relief='raised', bg='white')
        self.collapsiblePanelWhichFields.grid(sticky='w', row=4, pady=5)

        # Create Select metadata fields frame, Get Fields button and help text
        self.frameWhichFields = Frame(self.collapsiblePanelWhichFields.subFrame, bg='white')
        self.buttonGetFieldNames = Button(
            self.frameWhichFields,
            text='List metadata field names',
            bg=appPrimaryGreyColor, fg='white',
            width=175, height=30,
            command=lambda: get_parent_field_names(
                metadatablockData=get_metadatablock_data(
                    installationUrl=get_installation_url(self.comboboxInstallationUrl.get().strip()),
                    metadatablockName='citation'),
                listbox=self.listboxSelectFieldNames))

        labelSelectFieldNamesHelpTextString = (
            'Only fields in the Citation metadatablock are listed')
            # '\r\rIf you choose fields that are made up of multiple child fields, '
            # 'the CSV files will contain what\'s entered in each child field. '
            # 'For example, if you choose Keyword, the CSV files will contain the '
            # 'values of the Keyword field\'s three child fields: Term, '
            # 'Vocabulary and Vocabulary URL')
        self.labelSelectFieldNamesHelpText = Label(
            self.frameWhichFields,
            text=labelSelectFieldNamesHelpTextString,
            font='Helvetica', anchor='w', 
            wraplength=380, justify='left', fg='grey', bg='white')
        
        # Create frames, label, and listbox for selecting field names
        self.frameSelectFieldNames = Frame(self.frameWhichFields, bg='white')
        self.frameSelectFieldNames.columnconfigure(0, weight=1)
        self.frameSelectFieldNames.columnconfigure(1, weight=180)

        self.labelSelectFieldNames = Label(
            self.frameSelectFieldNames,
            text='Select one or more metadata fields',
            font='Helvetica', bg='white', anchor='w')
        self.labelSelectFieldNamesAsterisk = Label(
            self.frameSelectFieldNames,
            text='*', fg='red', justify='left',
            font='Helvetica', anchor='w', bg='white')
        self.frameListboxSelectFieldNames = Frame(self.frameSelectFieldNames, bg='white')
        values = StringVar()
        self.listboxSelectFieldNames = Listbox(
            self.frameListboxSelectFieldNames,
            width = 42, height=8, borderwidth=1,
            listvariable=values, selectmode=MULTIPLE, exportselection=0)

        # Create scrollbar for listbox
        self.scrollbarSelectFieldNames = Scrollbar(
            self.frameListboxSelectFieldNames, orient='vertical')
        self.scrollbarSelectFieldNames.config(
            command=self.listboxSelectFieldNames.yview)

        # Create frame and buttons for selecting and deselecting all listbox selections
        self.framelistboxButtons = Frame(
            self.frameWhichFields, bg='white')
        self.buttonSelectAll = Button(
            self.framelistboxButtons,
            text='Select all', width=120,
            command=lambda: select_all(self.listboxSelectFieldNames))
        self.buttonClearSelections = Button(
            self.framelistboxButtons, 
            text='Clear selections', width=120, 
            command=lambda: clear_selections(self.listboxSelectFieldNames))

        # Place frames, buttons, labels and help text for getting and selecting metadata field names
        self.frameWhichFields.grid(sticky='w', row=0, pady=10)
        self.buttonGetFieldNames.grid(sticky='w', row=0)
        self.labelSelectFieldNamesHelpText.grid(sticky='w', row=1)

        self.frameSelectFieldNames.grid(sticky='w', row=2, pady=10)
        self.labelSelectFieldNames.grid(sticky='w', column=0, row=0)
        self.labelSelectFieldNamesAsterisk.grid(sticky='w', column=1, row=0)

        self.frameListboxSelectFieldNames.grid(sticky='w', row=3, columnspan=2)
        self.listboxSelectFieldNames.grid(sticky='w', row=0)
        self.scrollbarSelectFieldNames.grid(sticky=N+S+W, column=1, row=0)
        
        self.framelistboxButtons.grid(sticky='w', row=4, pady=5)
        self.buttonSelectAll.grid(sticky='w', column=0, row=1)
        self.buttonClearSelections.grid(sticky='w', column=1, row=1)

        # Add scrollbar to listbox for select metadata field names
        self.listboxSelectFieldNames.config(
            yscrollcommand=self.scrollbarSelectFieldNames.set)

        # Create Get Metadata frame, button and validation error message text
        self.framebuttonGetMetadata = Frame(self.mainFrame, bg='white')

        # When button is pressed, get the list of dataset PIDs from 
        # the get_datasets_from_search_url command that was run
        self.buttonGetMetadata = Button(
            self.framebuttonGetMetadata, 
            text='Get metadata', bg=appPrimaryBlueColor,
            fg='white', width=423, height=40,
            font=font.Font(family='Helvetica', size=15, weight='bold'),
            command=lambda: get_dataset_metadata(
                    rootWindow=self.framebuttonGetMetadata,
                    progressText=self.progressTextGetMetadata,
                    progressLabel=self.labelProgressTextGetMetadata,
                    noMetadataText=self.fieldsWithNoMetadataText,
                    noMetadataLabel=self.labelFieldsWithNoMetadata,
                    installationUrl=get_installation_url(self.comboboxInstallationUrl.get().strip()),

                    # get_dataset_metadata function needs to turn this string into a list of pids
                    datasetPidString=self.textBoxCollectionDatasetPIDs.get('1.0', END),

                    parentFieldTitleList=get_listbox_values(self.listboxSelectFieldNames),

                    directoryPath=get_directory_path(), # function that asks user for directory
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
            font='Helvetica', anchor='w',
            wraplength=400, justify='left', fg='red', bg='white')

        # Place Get Metadata frame and button
        self.framebuttonGetMetadata.grid(sticky='w', row=5, pady=15)
        self.buttonGetMetadata.grid(sticky='w', column=0, row=0)
        self.labelFieldsWithNoMetadata.grid(sticky='w', row=1)

        # # Create progress bar and label
        # self.getMetadataProgressBar = Progressbar(
        #     self.framebuttonGetMetadata,
        #     length=200,
        #     maximum=self.total,
        #     value=0)
        # self.getMetadataProgressLabel = Label(
        #     self.framebuttonGetMetadata,
        #     text='0 of %s (0%%)' % (self.total),
        #     bg='white')

        # self.getMetadataProgressBar.grid(sticky='w', row=2)
        # self.getMetadataProgressLabel.grid(sticky='w', row=3)


    # def open_url(self, url):
    #     webbrowser.open_new(url)

    def stop(self):
        # if self.cancel_id is not None:
        self.textBox.after_cancel(self.cancel_id)
        self.cancel_id = None

    # Hide all frames function
    def hide_choose_dataset_frames(self):
        self.frameCollectionURL.grid_forget()
        self.frameSearchURL.grid_forget()
        # self.frameEnterUrls.grid_forget()
        # self.frameDatasetList.grid_forget()
        # self.frameBrowseJSONFiles.grid_forget()
        

    def get_datasets_method(self, *args):
        if self.dropdownOptionSelected.get()  == 'In a Dataverse Collection':
            self.hide_choose_dataset_frames()
            self.frameCollectionURL.grid(sticky='w', row=1, pady=0)

        elif self.dropdownOptionSelected.get() == 'From a Search URL':
            self.hide_choose_dataset_frames()
            self.frameSearchURL.grid(sticky='w', row=1, pady=0)

        # elif self.dropdownOptionSelected.get() == 'From dataset URLs or PIDs':
        #     self.hide_choose_dataset_frames()
        #     self.frameEnterUrls.grid(sticky='w', row=1, pady=0)

        # elif self.dropdownOptionSelected.get() == 'From a list of dataset PIDs':
        #     self.hide_choose_dataset_frames()
        #     self.frameDatasetList.grid(sticky='w', row=1, pady=0)

        # elif self.dropdownOptionSelected.get() == 'From Dataverse JSON export files':
        #     self.hide_choose_dataset_frames()
        #     self.frameBrowseJSONFiles.grid(sticky='w', row=1, column=0, pady=0)


    # def get_stringvar(self, event):
    #     self.entryDatasetPidsStringvar.set(entryDatasetPids.get('1.0', END))


    # def clear_error_message(self, *args):
    #     self.x = apikey.get()
    #     self.datasetIds = self.entryDatasetPidsStringvar.get()[:-1]
    #     # "[:-1]" removes newline character from scrolled text box

    #     if self.x and self.datasetIds and self.datasetIds != '\n':
    #         self.labelEntriesRequired.grid_forget()
