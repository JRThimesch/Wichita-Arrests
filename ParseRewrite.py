import PyPDF2
import re, json

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

def getTrimmedPageText(_pageObject):
    pageTextFull = _pageObject.extractText()

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

def getNames(_pdfObj):
    # PDF files store hidden characteristics within each file
    # Names of each person arrested are included here, so it's possible to get all names
    nameArray = []
    for outline in _pdfObj.outlines[1]:
        try:
            # Some arrests happen at the same time, leading to multiple entries
            for name in outline:
                nameArray.append(name.title)
        except:
            # Exception occurs specifically when there is no title at outline[0]
            # This also signals no name, so skips
            continue
    return nameArray

def sliceAtNames(_fullText, _nameArray):
    try:
        name = _nameArray.pop()
        partitionedText = _fullText.partition(name)
        _fullText = partitionedText[0]
        fullRecord = partitionedText[1] + partitionedText[2]
        sliceAtNames(_fullText, _nameArray)
    except IndexError:
        return None
    
if __name__ == "__main__":
    with open('text.txt', 'w') as file:
        pdfObject = openPDF('PDFs/08-12-19.pdf')
        nameArray = getNames(pdfObject)
        #print(nameArray)
        
        fullText = ''
        for page in getPageRange(pdfObject):
            pageObject = pdfObject.getPage(page)
            pageText = getTrimmedPageText(pageObject)
            pageTextSpaced = fixTextSpacing(pageText)
            fullText += pageTextSpaced + ' '
            
        sliceAtNames(fullText, nameArray)
        file.write(fullText)
        #print(fullText)