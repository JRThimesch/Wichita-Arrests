from bs4 import BeautifulSoup
import PyPDF2
import re, os, datetime, logging
import urllib.parse, urllib.request

arrestLink = re.compile('arrest', flags = re.I)
logging.basicConfig(level=logging.INFO, filename='downloads.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')

def getPageContent(_URL):
    # Returns a soup object of the page's content
    with urllib.request.urlopen(_URL) as response:
        content = response.read()
    return BeautifulSoup(content, features = 'html.parser')

def getURLPaths(_soup):
    # Returns list of paths on the page that contain 'arrest', case-insensitive
    return [link.get('href') for link in _soup.find_all('a') if arrestLink.search(str(link.get('href')))]

def getFullURLs(_soup):
    # Return a Full URL to download
    domain = 'https://www.wichita.gov'
    return [domain + urllib.parse.quote(path) for path in getURLPaths(_soup)]

def getPDFFileNameFromURL(_URL):
    # URLs look something like .../11-05-19%20arrest%20report.pdf
    # rpartition to get /11-05-19%20arrest%20report.pdf then partition the to get the name
    pdfName = _URL.rpartition('/')[2]
    pdfName = pdfName.partition('%')[0]
    pdfName += '.pdf'
    return pdfName 

def getAlreadyExistingPDFs(_path = 'PDFs/'):
    # Returns list of .pdfs that are within the path
    alreadyExistingFiles = os.listdir(_path)
    return [file for file in alreadyExistingFiles if file.endswith('.pdf')]

def doesPDFExist(_pdf):
    return _pdf in getAlreadyExistingPDFs()

def downloadPDF(_URL, _pdfName):
    # Write pdf content from URL to file of pdfName
    response = urllib.request.urlopen(_URL)
    downloadPath = 'PDFs/' + _pdfName
    logging.info('Downloading ' + _pdfName)
    with open(downloadPath, 'wb') as f:
        f.write(response.read())
        logging.info(_pdfName + ' successfully downloaded.')
        
def getFormattedDateFromFileName(_pdfName):
    # The date within the PDFs are of different format to those in the filename
    date = _pdfName.replace('.pdf', '')
    try:
        date = datetime.datetime.strptime(date, "%m-%d-%y").strftime("%m/%d/%Y")
    except ValueError:
        # Rarely, the format of the filename is different from the standard
        date = datetime.datetime.strptime(date, "%m-%d-%Y").strftime("%m/%d/%Y")
    return date

def openPDF(_filePath):
    pdfFile = open(_filePath, 'rb')
    pdfObject = PyPDF2.PdfFileReader(pdfFile)
    return pdfObject

def getPageRange(_pdfObj):
    numOfPages = _pdfObj.getNumPages()
    return range(numOfPages)

def getTextFromPages(_pdfObj):
    combinedText = ''
    for page in getPageRange(_pdfObj):
        pageObject = _pdfObj.getPage(page)
        combinedText += pageObject.extractText()
    return combinedText

def validatePDF(_pdfName):
    # Sometimes the wrong PDF is uploaded to Wichita PD's website
    # To check the validity, check for the date of the PDF to be within the PDF itself
    validatePath = 'PDFs/' + _pdfName
    formattedDate = getFormattedDateFromFileName(_pdfName)
    pdfObject = openPDF(validatePath)
    pdfText = getTextFromPages(pdfObject)
    logging.info('Validating ' + _pdfName)
    return formattedDate in pdfText

def removeInvalidPDF(_pdfName):
    # In the case where a PDF is invalid, it is of no use to store it, so just delete it
    removalPath = 'PDFs/' + _pdfName
    os.remove(removalPath)
    print('\t************')
    print('\tDate mismatch:', _pdfName)
    print('\t************')
    logging.warning('Date mismatch detected in ' + _pdfName)

if __name__ == "__main__":
    soupContent = getPageContent('https://www.wichita.gov/WPD/Pages/PublicRelations.aspx')
    URLs = getFullURLs(soupContent)

    for URL in URLs:
        pdfName = getPDFFileNameFromURL(URL)
        if doesPDFExist(pdfName):
            print(pdfName, 'already downloaded!')
            continue

        downloadPDF(URL, pdfName)

        if not validatePDF(pdfName):
            removeInvalidPDF(pdfName)
        
        logging.info(pdfName + ' validated!')
        print(pdfName, 'successfully downloaded and validated!')
