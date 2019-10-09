import PyPDF2
import os, re, json

HEADER_STR = 'Incidents with Offenses / Warrants'
HEADER_OFFSET = len('Incidents with Offenses / Warrants')

def getPDFs(_path):
    files = os.listdir(_path)
    return[_path + file for file in files if file.endswith('.pdf')]

def openPDF(_filePath):
    pdfFile = open(_filePath, 'rb')
    pdfObject = PyPDF2.PdfFileReader(pdfFile)
    return pdfObject

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

def getPageRange(_pdfObj):
    numOfPages = _pdfObj.getNumPages()
    return range(numOfPages)

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

def regexSplitandJoin(_str, _pattern):
    return ' '.join(re.split(_pattern, _str))

def fixTextSpacing(_fullText):
    _fullText = regexSplitandJoin(_fullText, '(\d{2}/\d{2}/\d{4})')
    _fullText = regexSplitandJoin(_fullText, '(\d{2}:\d{2})')
    _fullText = _fullText.replace('Sedgwick County Warrant', ' Sedgwick County Warrant ')
    findRaceGender(_fullText)
    return ' '.join(_fullText.split())

def findNthRegex(_str, _pattern, n):
    return re.findall(_pattern, _str)[n - 1]

def getRowBeforeEmpty(_fullText):
    # Dates occur only once per record, making them useful for finding a new record
    # By finding the second time and subtracting an offset, the empty name can be fixed
    secondTime = findNthRegex(_fullText, '(\d{2}:\d{2})', 2)
    secondTimeIndex = _fullText.index(findNthRegex(_fullText, '(\d{2}:\d{2})', 2))
    sliceIndex = secondTimeIndex - 11
    return _fullText[:sliceIndex]

def getRows(_fullText, _nameArray):
    try:
        for index, name in enumerate(_nameArray):
            try:
                # Search for the next name to get full row
                nextName = _nameArray[index + 1]
                partitionedText = _fullText.partition(nextName)

                # Partitioning will not work correctly if there are same names in a row
                # A second partition needs to be done on the first partition
                if name == nextName:
                    secondPartition = partitionedText[2].partition(nextName)
                    _fullText = secondPartition[1] + secondPartition[2]
                    yield partitionedText[1] + secondPartition[0]
                    continue
                
                # Yield before the found name and remove the row from the text
                _fullText = partitionedText[1] + partitionedText[2]
                yield partitionedText[0]

            except ValueError:
                # Occurs when an empty name is in the nameArray
                rowBeforeEmpty = getRowBeforeEmpty(_fullText)
                yield rowBeforeEmpty
                _fullText = 'NO NAME FOUND ' + _fullText.replace(rowBeforeEmpty, '')
                continue
    except IndexError:
        # An index error exception occurs at last in list
        # At this point _fullText is trimmed of all but the last record
        yield _fullText

if __name__ == "__main__":
    with open('text.txt', 'w') as file:
        for pdf in getPDFs('PDFs/'):
            pdfObject = openPDF(pdf)
            nameArray = getNames(pdfObject)
            
            fullText = ''
            for page in getPageRange(pdfObject):
                pageObject = pdfObject.getPage(page)
                pageText = getTrimmedPageText(pageObject)
                pageTextSpaced = fixTextSpacing(pageText)
                fullText += pageTextSpaced + ' '
                
            for row in getRows(fullText, nameArray):
                #print(row)
                file.write(row + '\n')
