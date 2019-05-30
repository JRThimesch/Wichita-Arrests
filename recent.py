import os

def findAlreadyExisting(_ext = ''):
    files = []
    for root, directories, files in os.walk('.', topdown=False):
        for file in files:
            if file.endswith(_ext):
                #print('ass' + os.path.splitext(file)[0])
                files.append(os.path.splitext(file)[0])
    return files

def doesExist(_file, _ext = ''):
    files = findAlreadyExisting(_ext)

    for i in files:
        i += _ext

    if _file in files:
        return True
    
    return False