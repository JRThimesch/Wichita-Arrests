import PyPDF2
import os, re, json
import pandas as pd

HEADER_STR = 'Incidents with Offenses / Warrants'
HEADER_OFFSET = len('Incidents with Offenses / Warrants')

def getPDFs(_path):
    files = os.listdir(_path)
    return[_path + file for file in files if file.endswith('.pdf')]

def openPDF(_filePath):
    pdfFile = open(_filePath, 'rb')
    pdfObject = PyPDF2.PdfFileReader(pdfFile)
    return pdfObject

def getNamesFromPDF(_pdfObj):
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

def combinePages(_pdfObj):
    combinedText = ''
    for page in getPageRange(_pdfObj):
        pageObject = _pdfObj.getPage(page)
        trimmedPagedText = getTrimmedPageText(pageObject)
        combinedText += trimmedPagedText + ' '
    return combinedText

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

def findNthRegex(_str, _pattern, n):
    return re.findall(_pattern, _str)[n - 1]

def getRowBeforeEmpty(_fullText):
    # Dates occur only once per record, making them useful for finding a new record
    # By finding the second time and subtracting an offset, the empty name can be fixed
    secondTime = findNthRegex(_fullText, '(\d{2}:\d{2})', 2)
    secondTimeIndex = _fullText.index(findNthRegex(_fullText, '(\d{2}:\d{2})', 2))
    sliceIndex = secondTimeIndex - 11
    return _fullText[:sliceIndex]

def getExpandedGenderInfo(_abbreviation):
    replacements = {
        'W' : 'WHITE',
        'B' : 'BLACK',
        'A' : 'ASIAN',
        'I' : 'INDIAN',
        'H' : 'HISPANIC',
        'M' : 'MALE ',
        'F' : 'FEMALE ',
        'U' : 'UNKNOWN'
    }

    try:
        abbreviationList = [replacements[char] for char in _abbreviation]
    except:
        print('Unknown key in abbreviation:', _abbreviation)
    return ' '.join(abbreviationList)

def findRaceGender(_fullText):
    # The index for times is useful as the gender info is contained right after
    times = re.findall('(\d{2}:\d{2})', _fullText)
    lastIndex, spacingOffset = 0, 6
    genderChar = ('M', 'F')
    for time in times:
        # lastIndex is used to ensure duplicate times are not a problem
        currentIndex = _fullText.find(time, lastIndex)
        currentIndexWithOffset = currentIndex + spacingOffset
        
        genderInfo = _fullText[currentIndexWithOffset:currentIndexWithOffset + 3]

        # Remove last character if it is not actual info
        if not genderInfo.endswith(genderChar):
            genderInfo = genderInfo[:-1]

        expandedGenderInfo = getExpandedGenderInfo(genderInfo)
        endOfGenderInfoIndex = currentIndexWithOffset + len(genderInfo)

        # Replacement of the genderInfo with expandedGenderInfo
        # Cannot use .replace as that will replace parts in names/arrests/etc.
        _fullText = _fullText[:currentIndexWithOffset] + expandedGenderInfo + _fullText[endOfGenderInfoIndex:]
        lastIndex = currentIndex + len(expandedGenderInfo)
    return _fullText

def isPartOfAddress(_word):
    if not _word.isalpha() and not _word.isdigit() and not _word[0].isdigit():
        return False
    else:
        return True

def addressSpacing(_fullText):
    # Address appears right after gender info
    # 'MALE' appears in both MALE and FEMALE, making it a useful split
    sliceChar = ''
    textSplitAtMale = _fullText.split('MALE ')
    newText = textSplitAtMale[1]
    #print(newText)
    for substring in textSplitAtMale[1:]:
        for word in substring.split():
            if not isPartOfAddress(word):
                for char in word:
                    if not char.isalpha():
                        sliceChar = char
                        break
                

                break
        newText += 'MALE ' + substring[:substring.find(sliceChar)] + ' ' + substring[substring.find(sliceChar):]
    return newText

def fixFullTextSpacing(_fullText):
    _fullText = regexSplitandJoin(_fullText, '(\d{2}/\d{2}/\d{4})')
    _fullText = regexSplitandJoin(_fullText, '(\d{2}:\d{2})')
    _fullText = findRaceGender(_fullText)
    #_fullText = addressSpacing(_fullText)
    _fullText = regexSplitandJoin(_fullText, '(\d{2}C\d{6})')
    _fullText = regexSplitandJoin(_fullText, '(\d{2}\w{2}\d{6})')
    _fullText = _fullText.replace('Sedgwick County Warrant', ' Sedgwick County Warrant ')

    return ' '.join(_fullText.split())

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
                _fullText = 'No name found. ' + _fullText.replace(rowBeforeEmpty, '')
                continue

    except IndexError:
        # An index error exception occurs at last in list
        # At this point _fullText is trimmed of all but the last record
        yield _fullText

def findFirstDigit(_str):
    firstDigit = re.search('\d', _str)
    return firstDigit.start()

def getNamesFromRow(_rowText):
    # First digit signals the beginning of the date, ergo, the end of the name entry
    sliceIndex = findFirstDigit(_rowText) - 1
    name = _rowText[:sliceIndex]
    return name

def getDateAndBirthdateFromRow(_rowText):
    datesAndBirthdates = re.findall('\d{2}/\d{2}/\d{4}', _rowText)
    try:
        birthdate, date = datesAndBirthdates[0], datesAndBirthdates[1]
    except IndexError:
        birthdate, date = 'No birthdate found.', datesAndBirthdates[0]
    return birthdate, date

def getAgeFromRow(_rowText):
    try:
        age = re.search('\d{2}\/\d{2}\/\d{4}(.+?)\d{2}\/\d{2}\/\d{4}', _rowText).group(1)
        return age.strip()
    except AttributeError:
        return 'No age found.'

def getRaceFromRow(_rowText):
    pattern = '\d{2}:\d{2}(.+?)' + getSexFromRow(_rowText)
    race = re.search(pattern, _rowText).group(1)
    return race.strip()

def getSexFromRow(_rowText):
    if 'FEMALE' in _rowText:
        return 'FEMALE'
    else:
        return 'MALE'

def getTimeFromRow(_rowText):
    return re.search('(\d{2}:\d{2})', _rowText).group(1)

def trimOutWarrantsFromIncidents(_incidentText):
    warrantPattern = '(\d{2}[A-Z]{2}\d{6})'
    try:
        warrantMatchIndex = re.search(warrantPattern, _incidentText).start()
        _incidentText = _incidentText[:warrantMatchIndex - 1]
    except AttributeError:
        pass
    return _incidentText.strip()

def trimOutExcessInfoFromIncidents(_incidentText):
    incidentPattern = '\d{2}C\d{6}'
    try:
        incidentMatchIndex = re.search(incidentPattern, _incidentText).start()
        _incidentText = _incidentText[incidentMatchIndex:]
        return _incidentText
    except AttributeError:
        return 'No incidents.'

def getListOfIncidents(_incidentText):
    incidentIdPattern = '\s?\d{2}C\d{6,}\s\d{3,}\s-\s|\s?\d{2}C\d{6}\s?'
    listOfIncidentsUntrimmed = re.split(incidentIdPattern, _incidentText)
    listOfIncidentsTrimmed = list(filter(None, listOfIncidentsUntrimmed))
    return listOfIncidentsTrimmed

def getCleanedIncidents(_incidentText):
    incidentCodePattern = '\d{3,}\w?\s-\s'
    cleanedIncidents = [', '.join(re.split(incidentCodePattern, e)) for e in getListOfIncidents(_incidentText)]
    return cleanedIncidents

def getIncidentsFromRow(_rowText):
    incidentText = _rowText
    incidentText = trimOutWarrantsFromIncidents(incidentText)
    incidentText = trimOutExcessInfoFromIncidents(incidentText)
    cleanedIncidents = getCleanedIncidents(incidentText)
    return cleanedIncidents

def getWarrantsFromRow(_rowText):
    warrantPattern = '(\d{2}[A-Z]{2}\d{6})'
    warrantTags = re.findall(warrantPattern, _rowText)
    return warrantTags

if __name__ == "__main__":
    with open('text.txt', 'w') as file:
        for pdf in getPDFs('PDFs/'):
            pdfObject = openPDF(pdf)
            nameArray = getNamesFromPDF(pdfObject)
            fullText = combinePages(pdfObject)
            fullTextSpaced = fixFullTextSpacing(fullText)
            rowsAsList = []
            
            for row in getRows(fullTextSpaced, nameArray):
                birthdate, date = getDateAndBirthdateFromRow(row)
                file.write(row + '\n')
                rowsAsList.append([
                    getNamesFromRow(row),
                    birthdate,
                    getAgeFromRow(row),
                    getRaceFromRow(row),
                    getSexFromRow(row),
                    date,
                    getTimeFromRow(row),
                    None,
                    None,
                    getIncidentsFromRow(row),
                    getWarrantsFromRow(row)
                ])
            
            df = pd.DataFrame(rowsAsList, columns=[
                'Name', 'Birthdate', 'Age', 
                'Race', 'Sex', 'Date', 
                'Time', 'Address', 'Arrests', 
                'Incidents', 'Warrants'
            ])

            print(df)
                
