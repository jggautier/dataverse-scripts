# Create executable file for Dataverse repository curation assistant

import PyInstaller.__main__
import os
import shutil

# Create executable and other files
PyInstaller.__main__.run([
    'dataverse_repository_curation_assistant_main.py',
    '--windowed',
    '--name=Dataverse_repository_curation_assistant'
])

# Move .app file to main directory and rename
shutil.move(
    'dist/Dataverse_repository_curation_assistant.app',
    'Dataverse repository curation assistant.app')

# Delete remaining directories and their files
shutil.rmtree('dist')
shutil.rmtree('build')
os.remove('Dataverse repository curation assistant.spec')

# Zip the Dataverse repository curation assistant.app file
# shutil.make_archive(
#     base_name='Dataverse repository curation assistant.app', 
#     format='zip')
