from curation_app_functions import *
from get_metadata_as_csv_files import *
from delete_published_datasets import *
# from PIL import ImageTk, Image
from tkinter import Tk, ttk, Frame, Label, IntVar, StringVar
from tkinter.ttk import OptionMenu
# from tkmacosx import Button
from ttkthemes import ThemedTk
# import webbrowser

def hide_choose_dataset_frames():
    getMetadataAsCSVsFrame.grid_forget()
    deletePublishedDatasetsFrame.grid_forget()


def show_task_frame(*args):
    if dropdownOptionSelected.get()  == 'Get metadata as CSV files':
        hide_choose_dataset_frames()
        getMetadataAsCSVsFrame.grid(sticky='w', row=4, padx=20, pady=0)
        frameChooseTaskBG.config(background=appPrimaryBlueColor)
        frameChooseTask.config(background=appPrimaryBlueColor)
        labelChooseTask.config(background=appPrimaryBlueColor)

    elif dropdownOptionSelected.get() == 'Delete published datasets':
        hide_choose_dataset_frames()
        deletePublishedDatasetsFrame.grid(sticky='w', row=4, padx=20, pady=0)
        frameChooseTaskBG.config(background=appPrimaryRedColor)
        frameChooseTask.config(background=appPrimaryRedColor)
        labelChooseTask.config(background=appPrimaryRedColor)


root = ThemedTk(theme='arc')
root.title('Curation assistant')
root.configure(background='white')
root.resizable(False, True)


appPrimaryBlueColor = '#286090'
appPrimaryRedColor = '#BF0000'
appPrimaryGreyColor = '#6E6E6E'

# Create and place frame and labels for name and description of the app
frameAppHeading = Frame(root, bg='white')
frameAppHeading.grid(row=0, sticky='w', padx=20, pady=10)

labelAppHeading = Label(
    frameAppHeading, 
    text='Curation assistant', 
    bg='white', font=('Arial', 20, 'bold'),
    anchor='w')
labelAppHeading.grid(row=0, sticky='w')
appDescrtionText = (
    'Automate tasks in Dataverse repositories')
labelAppDescription = Label(
    frameAppHeading,
    text=appDescrtionText,
    wraplength=400, justify='left',
    bg='white', anchor='w')
labelAppDescription.grid(row=1, sticky='w')

# Create app frames, which are loaded from the show_task_frame
#function when user chooses from list of tasks
getMetadataAsCSVsFrame = getMetadataAsCSVsFrame(root)
deletePublishedDatasetsFrame = deletePublishedDatasetsFrame(root)

# Create and place frame for choosing task
frameChooseTaskBG = Frame(root, bg=appPrimaryBlueColor)
frameChooseTaskBG.grid(row=1, sticky='w', padx=20, pady=10)

# Create and place frame for components in the frameChooseTaskBG frame
frameChooseTask = Frame(frameChooseTaskBG, bg=appPrimaryBlueColor)
frameChooseTask.grid(row=0, sticky='w', padx=10, pady=10)

# Create Select datasets label and dropdown for menu
labelChooseTask = Label(
    frameChooseTask,
    text='What would you like to do?',
    fg='white', font=('Arial', 14, 'bold'),
    bg=appPrimaryBlueColor, 
    width=49, anchor='w')
labelChooseTask.grid(row=0, sticky='n')
taskOptions = [
    'Get metadata as CSV files',
    'Delete published datasets']
dropdownOptionSelected = StringVar()
# dropdownOptionSelected.set('Select...')
dropdownOptionSelected.trace('w', show_task_frame)
dropdownMenuChooseDatasets = OptionMenu(
    frameChooseTask,
    dropdownOptionSelected,
    taskOptions[0], *taskOptions)
dropdownMenuChooseDatasets.grid(row=1, sticky='nw', pady=5)

root.mainloop()
