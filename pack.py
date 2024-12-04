import os
import zipfile

zipname = 'HonSagashi.zip'
files = ['__init__.py', 'LICENSE']

if os.path.exists(zipname):
    print("Old packed file found. Delete.")
    os.remove(zipname)

with zipfile.ZipFile(zipname, 'w') as zipf:
    for file in files:
        zipf.write(file)

print("Packed successfully.")