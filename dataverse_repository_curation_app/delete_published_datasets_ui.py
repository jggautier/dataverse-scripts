# App for getting the metadata of datasets as CSV files

from dataverse_repository_curation_app_functions import *
import json
import os
import requests
import sys
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


class deletePublishedDatasetsFrame(Frame):

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

        textTaskDescription = (
            'Dataverse installation administrators with "superuser" API Tokens '
            'can delete published datasets in their Dataverse repository'
            '\r\rUse this app to remove all datasets in a Dataverse Collection, '
            'from a search query URL, or by entering dataset URLs or DOIs'
            '\r\rHarvested datasets are always excluded and datasets will be '
            'excluded if they\'re linked in but not owned by the given '
            'Dataverse Collection')

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
            self.root,
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
        self.frameApiToken.grid(sticky='w', row=1)
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

        # Create and place collapsible panel for choosing datasets
        self.collapsiblePanelChooseDatasets = collapsiblePanel(
            self.root,
            text='Which datasets?',
            default='closed', relief='raised', bg='white')
        self.collapsiblePanelChooseDatasets.grid(sticky='w', row=3, pady=5)

        # Create and place frame for all "Choose dataset" frames
        self.frameChooseDatasets = Frame(self.collapsiblePanelChooseDatasets.subFrame, bg='white')
        self.frameChooseDatasets.grid(row=1)

        # Create Get Metadata frame, button and validation error message text
        self.frameDeleteDatasetsButton = Frame(self.root, bg='white')

        # When button is pressed, get the list of dataset PIDs from 
        # the textBoxCollectionDatasetPIDs textbox
        self.buttonDeleteDatasets = Button(
            self.frameDeleteDatasetsButton, 
            text='Delete datasets', bg=appPrimaryRedColor,
            fg='white', width=423, height=40,
            font=font.Font(size=15, weight='bold'),
            command=lambda: delete_published_datasets(
                    rootWindow=self.frameDeleteDatasetsButton,
                    progressText=self.progressTextDeleteDatasets,
                    progressLabel=self.labelProgressTextDeleteDatasets,
                    notDeletedText=self.notDeletedText,
                    notDeletedLabel=self.labelNotDeletedDatasets,
                    installationUrl=get_installation_url(self.comboboxInstallationUrl.get().strip()),
                    datasetPidString=self.textBoxCollectionDatasetPIDs.get('1.0', END),
                    apiKey=self.entryApiToken.get().strip()
                    )
                )

        self.progressTextDeleteDatasets = StringVar()
        self.labelProgressTextDeleteDatasets = Label(
            self.frameDeleteDatasetsButton,
            textvariable=self.progressTextDeleteDatasets,
            bg='white', anchor='w')

        self.labelProgressTextDeleteDatasets.config(fg='white')
        self.labelProgressTextDeleteDatasets.grid(sticky='w', row=1)

        self.notDeletedText = StringVar()
        self.labelNotDeletedDatasets = Label(
            self.frameDeleteDatasetsButton,
            textvariable=self.notDeletedText,
            anchor='w', fg='red', bg='white')

        # Place Get Metadata frame and button
        self.frameDeleteDatasetsButton.grid(sticky='w', row=5, pady=15)
        self.buttonDeleteDatasets.grid(sticky='w', column=0, row=0)

        # Create Enter Dataverse collection URL frame, field label, 
        # text box, load datasets button
        self.frameCollectionURL = Frame(self.frameChooseDatasets, bg='white')
        self.frameCollectionURL.columnconfigure(0, weight=1)
        self.frameCollectionURL.columnconfigure(1, weight=180)

        self.labelCollectionURL = Label(
            self.frameCollectionURL,
            text='Dataverse Collection URL',
            anchor='w', bg='white')
        self.labelCollectionURLAsterisk = Label(
            self.frameCollectionURL,
            text='*', fg='red', justify='left',
            anchor='w', bg='white')
        self.entryCollectionURL = Entry(
            self.frameCollectionURL, width=40)

        labelEntryCollectionURLHelpTextString = (
            'E.g. https://demo.dataverse.org/dataverse/name'
            '\r\rTo include all datasets in the repository, enter the repository\'s '
            'homepage URL, e.g. https://demo.dataverse.org, and click '
            '"Include datasets in all collections within this collection"')
        self.labelEntryCollectionURLHelpText = Label(
            self.frameCollectionURL,
            text=labelEntryCollectionURLHelpTextString,
            fg='grey', bg='white', 
            wraplength=380, justify='left', anchor='w')
        self.getSubdataverses = BooleanVar()
        self.checkboxGetSubdataverses = Checkbutton(
            self.frameCollectionURL,
            text="Include datasets in all collections within this collection", bg='white',
            variable=self.getSubdataverses, onvalue = True, offvalue = False)
        self.buttonLoadDatasets = Button(
            self.frameCollectionURL,
            text='Find the datasets',
            bg=appPrimaryGreyColor, fg='white',
            command=lambda: get_datasets_from_collection_or_search_url(
                rootWindow=self.framelabelProgressText,
                url=self.entryCollectionURL.get().strip(),
                progressLabel=self.labelProgressText,
                progressText=self.progressText,
                textBoxCollectionDatasetPIDs=self.textBoxCollectionDatasetPIDs,
                ignoreDeaccessionedDatasets=True,
                apiKey=self.entryApiToken.get().strip(),
                subdataverses=self.getSubdataverses.get()))
        
        # Place Enter Dataverse collection URL field label, text box, and validation error label 
        self.labelCollectionURL.grid(sticky='w', column=0, row=0)
        self.labelCollectionURLAsterisk.grid(sticky='w', column=1, row=0)
        self.entryCollectionURL.grid(sticky='w', row=1, columnspan=2)
        self.labelEntryCollectionURLHelpText.grid(sticky='w', row=2, columnspan=2)
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
            fg='black', bg='white', 
            wraplength=385, justify='left', anchor='w')

        self.labelSearchURL = Label(
            self.frameSearchURLField,
            text='Search URL',
            bg='white', anchor='w')
        self.labelSearchURLAsterisk = Label(
            self.frameSearchURLField,
            text='*', fg='red', justify='left',
            anchor='w', bg='white')
        self.entrySearchURL = Entry(
            self.frameSearchURLField, width=40)

        searchURLEntryHelpTextString = (
            'E.g. https://demo.dataverse.org/dataverse/demo/?q=surveys')

        self.labelSearchURLHelpText = Label(
            self.frameSearchURLField,
            text=searchURLEntryHelpTextString,
            fg='grey', bg='white', 
            wraplength=380, justify='left', anchor='w')
        self.buttonLoadDatasets = Button(
            self.frameSearchURLField,
            text='Find the datasets',
            bg=appPrimaryGreyColor, fg='white',
            width=140, height=30,
            command=lambda: get_datasets_from_collection_or_search_url(
                rootWindow=self.framelabelProgressText,
                url=self.entrySearchURL.get().strip(),
                progressLabel=self.labelProgressText,
                progressText=self.progressText,
                textBoxCollectionDatasetPIDs=self.textBoxCollectionDatasetPIDs,
                apiKey=self.entryApiToken.get().strip(),
                ignoreDeaccessionedDatasets=True))

        # Place Enter Search URL field label, text box, and validation error label
        self.frameAboutHelpText.grid(sticky='w', row=0)
        self.frameSearchURLField.grid(sticky='w', row=1, pady=5)
        self.labelAboutSearchURLHelpText.grid(sticky='w', row=0, pady=5)
        self.labelSearchURL.grid(sticky='w', column=0, row=1)
        self.labelSearchURLAsterisk.grid(sticky='w', column=1, row=1)
        self.entrySearchURL.grid(sticky='w', row=2, columnspan=2)
        self.labelSearchURLHelpText.grid(sticky='w', row=3, columnspan=2)
        self.buttonLoadDatasets.grid(sticky='w', row=4, columnspan=2, pady=10)
        
        # Create Enter dataset URLs or PIDs frame and field label,
        # and help text that will appear below the textBoxCollectionDatasetPIDs scrollbox
        self.frameEnterUrls = Frame(self.frameChooseDatasets, bg='white')
        self.labelEnterDatasets = Label(
            self.frameEnterUrls,
            text='Enter dataset URLs or PIDs', bg='white', anchor='w')

        # Place Enter dataset URLs or PIDs field label, text box, and validation error label
        self.labelEnterDatasets.grid(sticky='w', row=0)

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

        # Create frames and labels for indicating progress and showing results
        self.frameLoadDataSets = Frame(self.frameChooseDatasets, bg='white')
        self.frameLoadDataSets.grid(sticky='w', row=4, pady=5)

        self.framelabelProgressText = Frame(self.frameLoadDataSets, bg='white')

        self.progressText = StringVar()
        self.progressText.set('Datasets found: 0')
        self.labelProgressText = Label(
            self.framelabelProgressText,
            textvariable=self.progressText,
            bg='white', anchor='w', justify='left')
        self.labelProgressText.config(fg='white')
        self.labelProgressText.grid(sticky='w', row=0)

        self.frametextBoxCollectionDatasetPIDs = Frame(self.frameLoadDataSets, bg='white')
        # self.frametextBoxCollectionDatasetPIDs.grid(sticky='w', row=1)

        self.textBoxCollectionDatasetPIDs = ScrolledText(
            self.frametextBoxCollectionDatasetPIDs,
            width=45, height=8)
        self.textBoxCollectionDatasetPIDs.grid(sticky='w', row=1)

        self.labelDatasetPidsHelpText = Label(
            self.frametextBoxCollectionDatasetPIDs, 
            text='Enter each dataset URL or PID on a new line', 
            fg='grey', bg='white', 
            wraplength=380, justify='left', anchor='w')
        self.labelDatasetPidsHelpText.grid(row=3)

        # Create Select datasets label and dropdown for menu
        self.options = [
            'In a Dataverse Collection',
            'From a Search URL',
            'From dataset URLs or PIDs']
            # 'From a list of dataset PIDs',
            # 'From Dataverse JSON export files']
        self.dropdownOptionSelected = StringVar()
        self.dropdownOptionSelected.trace('w', self.get_datasets_method)
        self.dropdownMenuChooseDatasets = OptionMenu(
            self.collapsiblePanelChooseDatasets.subFrame,
            self.dropdownOptionSelected,
            self.options[0], *self.options)

        self.ttkStyle.configure('TMenubutton', foreground='black')

        # Place dropdown for menu
        self.dropdownMenuChooseDatasets.grid(sticky='w', row=0, pady=10)

    # Hide all frames function
    def hide_choose_dataset_frames(self):
        self.frameCollectionURL.grid_forget()
        self.frameSearchURL.grid_forget()
        self.frameEnterUrls.grid_forget()
        # self.frameDatasetList.grid_forget()
        # self.frameBrowseJSONFiles.grid_forget()
        # self.labelProgressTextDeleteDatasets.grid_forget()

        self.labelProgressTextDeleteDatasets.config(fg='white')
        

    def get_datasets_method(self, *args):
        if self.dropdownOptionSelected.get()  == 'In a Dataverse Collection':
            self.hide_choose_dataset_frames()
            self.frameCollectionURL.grid(sticky='w', row=1, pady=0)

            self.textBoxCollectionDatasetPIDs.configure(state ='normal')
            self.textBoxCollectionDatasetPIDs.delete('1.0', END)
            self.textBoxCollectionDatasetPIDs.configure(state ='disabled')

            # self.progressText.set('Datasets found: 0')
            self.labelProgressText.config(fg='white')
            self.framelabelProgressText.grid(sticky='w', row=0)

            self.labelDatasetPidsHelpText.grid_forget()

        elif self.dropdownOptionSelected.get() == 'From a Search URL':
            self.hide_choose_dataset_frames()
            self.frameSearchURL.grid(sticky='w', row=1, pady=0)

            self.textBoxCollectionDatasetPIDs.configure(state ='normal')
            self.textBoxCollectionDatasetPIDs.delete('1.0', END)
            self.textBoxCollectionDatasetPIDs.configure(state ='disabled')

            self.labelProgressText.config(fg='white')
            self.framelabelProgressText.grid(sticky='w', row=0)

            self.labelDatasetPidsHelpText.grid_forget()

        elif self.dropdownOptionSelected.get() == 'From dataset URLs or PIDs':
            self.hide_choose_dataset_frames()
            self.frameEnterUrls.grid(sticky='w', row=1, pady=0)

            self.textBoxCollectionDatasetPIDs.configure(state ='normal')
            self.textBoxCollectionDatasetPIDs.delete('1.0', END)
            self.framelabelProgressText.grid_forget()

            self.labelDatasetPidsHelpText.grid(row=3, sticky='w')

        # elif self.dropdownOptionSelected.get() == 'From a list of dataset PIDs':
        #     self.hide_choose_dataset_frames()
        #     self.frameDatasetList.grid(sticky='w', row=1, pady=0)

        # elif self.dropdownOptionSelected.get() == 'From Dataverse JSON export files':
        #     self.hide_choose_dataset_frames()
        #     self.frameBrowseJSONFiles.grid(sticky='w', row=1, column=0, pady=0)

