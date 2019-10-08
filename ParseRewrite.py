import PyPDF2
import re

HEADER_STR = 'Incidents with Offenses / Warrants'
HEADER_OFFSET = len('Incidents with Offenses / Warrants')

def openPDF(_filePath):
    pdfFile = open(_filePath, 'rb')
    pdfObject = PyPDF2.PdfFileReader(pdfFile)
    return pdfObject

def getPageRange(_pdfObj):
    numOfPages = _pdfObj.getNumPages()
    return range(numOfPages)

def regexSplitandJoin(_str, _pattern):
    return ' '.join(re.split(_pattern, _str))

def getTrimmedPageText(_page):
    pageTextFull = pdfObject.getPage(page).extractText()

    # Header is trimmed from the string defined at the top
    # An offset is added since the find function finds the beginning index
    headerTrimIndex = pageTextFull.find(HEADER_STR)
    headerTrimIndex += HEADER_OFFSET
    pageTextTrimmed = pageTextFull[headerTrimIndex:]

    # Last page contains a footer that must be removed
    # Last page is defined by the presence of ###Total Arrests:
    if 'Arrests:' in pageTextTrimmed:
        pageTextTrimmedList = pageTextTrimmed.split()
        pageTextTrimmedList = pageTextTrimmedList[:-2]
        pageTextTrimmed = ' '.join(pageTextTrimmedList)

    return pageTextTrimmed

def fixTextSpacing(_fullText):
    _fullText = regexSplitandJoin(_fullText, '(\d{2}/\d{2}/\d{4})')
    _fullText = regexSplitandJoin(_fullText, '(\d{2}:\d{2})')
    _fullText = _fullText.replace('Sedgwick County Warrant', ' Sedgwick County Warrant ')
    return _fullText

if __name__ == "__main__":
    with open('text.txt', 'w') as file:
        pdfObject = openPDF('PDFs/08-12-19.pdf')
        fullText = ''
        for page in getPageRange(pdfObject):
            pageText = getTrimmedPageText(page)
            pageTextSpaced = fixTextSpacing(pageText)
            fullText += pageTextSpaced + ' '
        file.write(fullText)
        print(fullText)