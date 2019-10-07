import PyPDF2

HEADER_STR = 'Incidents with Offenses / Warrants'
HEADER_OFFSET = len('Incidents with Offenses / Warrants')

def openPDF(_filePath):
    pdfFile = open(_filePath, 'rb')
    pdfObject = PyPDF2.PdfFileReader(pdfFile)
    return pdfObject

def getPageRange(_pdfObj):
    numOfPages = _pdfObj.getNumPages()
    return range(numOfPages)

def getTrimmedPageText(_pageText):
    pass

with open('text.txt', 'w') as file:
    pdfObject = openPDF('PDFs/08-12-19.pdf')
    for page in getPageRange(pdfObject):
        pageTextFull = pdfObject.getPage(page).extractText()
        headerTrimIndex = pageTextFull.find(HEADER_STR)
        headerTrimIndex += HEADER_OFFSET
        pageTextNoHeader = pageTextFull[headerTrimIndex:]
        file.write(pageTextNoHeader)
        print(pageTextNoHeader)