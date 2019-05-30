import os

def findAlreadyExisting(_path = '.', _ext = ''):
    files = os.listdir(_path)
    return[os.path.splitext(file)[0] for file in files if file.endswith(_ext)]


def doesExist(_file, _path = '.'):
    files = findAlreadyExisting(_path)

    if _file in files:
        return True
    
    return False