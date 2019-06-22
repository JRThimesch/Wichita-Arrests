from bs4 import BeautifulSoup
from tika import parser
import re
import os
import urllib.parse, urllib.request

def getLinks(_soup):
    # This doesn't look pretty but it returns a list of links, but only links that contain the string arrest and are part of the media reports
    return [str(link.get('href')) for link in _soup.find_all('a') if '/WPD/MediaReports/' and 'ARREST' in str(link.get('href')).upper()]

def findAlreadyExisting(_path = '.'):
    files = os.listdir(_path)
    return [file for file in files if file.endswith('.pdf')]

def doesFileExist(_file, _path = '.'):
    if _file in findAlreadyExisting(_path):
        return True
    return False

def getFileNames(_links):
    datePattern = '(\d{2}-\d{1,2}-\d{2})'
    fileNames = []
    for e in _links:
        match = re.search(datePattern, e)
        fileNames.append(match[0] + '.pdf')
    return fileNames

def getDownloadLink(_subdir):
    parsedLink = urllib.parse.quote(_subdir)
    url = 'https://www.wichita.gov' + parsedLink
    return url

def downloadPDF(_link, _location):
    response = urllib.request.urlopen(getDownloadLink(_link))
    with open(filePDF, 'wb') as f:
        f.write(response.read())
        f.close()

def getRawText(_pdf):
    return parser.from_file(_pdf)

def verifyDate(_pdf, _date):
    parsedText = getRawText(_pdf)
    toParse = ''.join(parsedText['content'])
    words = toParse.split()

    _date = _date.replace('-', '/')
    year = '20' + _date[-2:]
    _date = _date[:-2] + year

    if _date in words:
        return True
    else:
        return False

if __name__ == "__main__":
    url = 'https://www.wichita.gov/WPD/Pages/PublicRelations.aspx'
    
    with urllib.request.urlopen(url) as response:
        content = response.read()

    soup = BeautifulSoup(content, features = 'html.parser')
    pdfs = getLinks(soup)

    for i, e in enumerate(getFileNames(pdfs)):
        locationPDF = 'PDFs/'
        filePDF = locationPDF + e

        if doesFileExist(e, locationPDF):
            print(e + ' already downloaded!')
            continue

        print('Downloading', e, '...')

        downloadPDF(pdfs[i], filePDF)

        print('Verifying date...')

        date = os.path.splitext(e)[0]
        
        if verifyDate(filePDF, date):
            print(e, 'successfully downloaded!')
        else:
            os.remove(filePDF)
            print('\t************')
            print('\tDate mismatch:', e)
            print('\tDouble check on Wichita PD website')
            print('\t************')