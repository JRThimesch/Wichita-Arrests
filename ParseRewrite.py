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

def regexSplitandJoin(_pattern, _str):
    return ' '.join(re.split(_pattern, _str))

def regexFindNth(_pattern, _str, n):
    return re.findall(_pattern, _str)[n - 1]

def regexTrimLeftOrRight(_pattern, _str, _left = True):
    try:
        matchIndex = re.search(_pattern, _str).start()
        if _left:
            _str = _str[matchIndex:]
        else:
            _str = _str[:matchIndex - 1]
    except AttributeError:
        pass
    return _str

def regexSplitAndTrim(_pattern, _str):
    listSplit = re.split(_pattern, _str)
    listSplitAndTrimmed = list(filter(None, listSplit))
    return listSplitAndTrimmed

def getRowBeforeEmpty(_fullText):
    # Dates occur only once per record, making them useful for finding a new record
    # By finding the second time and subtracting an offset, the empty name can be fixed
    secondTime = regexFindNth('(\d{2}:\d{2})', _fullText, 2)
    secondTimeIndex = _fullText.index(regexFindNth('(\d{2}:\d{2})', _fullText, 2))
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

def fixFullTextSpacing(_fullText):
    _fullText = regexSplitandJoin('(\d{2}/\d{2}/\d{4})', _fullText)
    _fullText = regexSplitandJoin('(\d{2}:\d{2})', _fullText)
    _fullText = regexSplitandJoin('(\d{2}C\d{6})', _fullText)
    _fullText = regexSplitandJoin('(\d{2}\w{2}\d{6})', _fullText)
    _fullText = _fullText.replace('Sedgwick County Warrant', ' Sedgwick County Warrant ')
    _fullText = findRaceGender(_fullText)

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
    racePattern = '\d{2}:\d{2}(.+?)' + getSexFromRow(_rowText)
    race = re.search(racePattern, _rowText).group(1)
    return race.strip()

def getSexFromRow(_rowText):
    if 'FEMALE' in _rowText:
        return 'FEMALE'
    else:
        return 'MALE'

def getTimeFromRow(_rowText):
    return re.search('(\d{2}:\d{2})', _rowText).group(1)

def getTrimmedAddressText(_rowText):
    # Get as close to the actual address as possible
    address = _rowText.rpartition('MALE')[2]
    address = address.partition('-')[0]
    address = address.partition('#')[0]
    address = address.partition('No')[0]
    address = address.partition('Sedgwick')[0]
    return address.strip()

def findHighwaysInAddress(_address):
    # The only highways that appear are in the tuple 'highways'
    # If a highway is in the address, the address will get trimmed down to match it
    highways = ('I 135', 'K 96', 'I 235')
    if any(highway in _address for highway in highways):
        for highway in highways:
            partitionedAddress = _address.partition(highway)
            _address =  partitionedAddress[0] + partitionedAddress[1]
        return _address.strip()
    return None

def doesContainAlphaAndNum(_str):
    # True when a word contains both numbers and alpha
    # False when a word is either only numbers or only alpha
    return not _str.isdigit() and not _str.isalpha()

def doesAddressNeedTrimming(_str):
    # Returns True when the word is not an ordinal/alpha/numeric
    ordinals = ('ST', 'ND', 'RD', 'TH')
    return not _str.endswith(ordinals) and doesContainAlphaAndNum(_str)

def getLastWordInAddress(_addressList):
    # Last words in the address can be difficult to differentiate from arrest records
    # Often, the address contains a steet name concatenated with an arrest code
    # Example: E 2ND N215706
    # Besides '2ND', 'N215706' is the only word that contains both numbers and letters
    # By filtering out any ordinal/alpha/numeric words, the only word remaining is the last
    return list(filter(lambda word: doesAddressNeedTrimming(word), _addressList))[0]

def numOfCharUntilNumber(_str):
    # Returns the index of the last alpha character
    for i, char in enumerate(_str):
        if char.isalpha():
            continue
        return i

def doesBeginAndEndWithNum(_str):
    # ex. 19C123090 needs to be trimmed, but .isdigit() would return False
    return _str[0].isdigit() and _str[-1].isdigit()

def removeTrailingNumbersAndCodesFromList(_list):
    try:
        lastWordInList = _list[-1]
        if doesBeginAndEndWithNum(lastWordInList):
            del _list[-1]
            removeTrailingNumbersAndCodesFromList(_list)
    except IndexError:
        pass

def getTrimmedAddress(_addressText):
    try:
        addressTextList = _addressText.split()
        # Many times there is info that is incorrectly concatenated to the end of an address
        # By finding the last word, that info can be trimmed out
        lastWordInAddress = getLastWordInAddress(addressTextList)
        lastWordInAddressIndex = _addressText.find(lastWordInAddress)
        trimmedWordLenOffset = numOfCharUntilNumber(lastWordInAddress)
        trimIndex = lastWordInAddressIndex + trimmedWordLenOffset
        trimmedAddress = _addressText[:trimIndex]
    except:
        # Exception occurs when the address does NOT contain incorrectly concatenated info
        # However, sometime numbers remain at the end that aren't needed, so they're trimmed
        removeTrailingNumbersAndCodesFromList(addressTextList)
        trimmedAddress = ' '.join(addressTextList)

    return trimmedAddress

def getAddressFromRow(_rowText):
    addressText = getTrimmedAddressText(_rowText)        
    # Typically addresses do not end in numbers, however, highways do
    # There is no way to differentiate an address ending number from an arrest code
    # Therefore, the easiest solution is to look for those highways before continuing on
    highwayAddressFound = findHighwaysInAddress(addressText)
    if highwayAddressFound:
        return highwayAddressFound

    trimmedAddress = getTrimmedAddress(addressText)
    return trimmedAddress.strip()
    
def getListOfIncidents(_incidentText):
    incidentIdPattern = '\s?\d{2}C\d{6,}\s\d{3,}\s-\s|\s?\d{2}C\d{6}\s?'
    listOfIncidents = regexSplitAndTrim(incidentIdPattern, _incidentText)
    return listOfIncidents

def getCleanedIncidentsAndOffenses(_incidentText):
    # Incidents come with one or more offenses in them
    # The offenses need to be cleaned after the incident code has been cleaned
    offenseCodePattern = '\d{3,}\w?\s-\s'
    incidents = getListOfIncidents(_incidentText)
    cleanedIncidentsAndOffenses = []

    for incident in incidents:
        offensesTrimmed = regexSplitAndTrim(offenseCodePattern, incident)
        cleanedIncident = ', '.join(offensesTrimmed)
        cleanedIncidentsAndOffenses.append(cleanedIncident)
    return cleanedIncidentsAndOffenses

def getIncidentsFromRow(_rowText):
    incidentText = _rowText
    # Right trimming removes any warrants
    incidentTextRightTrimmed = regexTrimLeftOrRight('(\d{2}[A-Z]{2}\d{6})', incidentText, False)
    # Left trimming removes any before info not related to incidents
    incidentTextTrimmed = regexTrimLeftOrRight('\d{2}C\d{6}', incidentTextRightTrimmed)
    if incidentTextRightTrimmed == incidentTextTrimmed:
        return 'No incidents found.'
    cleanedIncidentsAndOffenses = getCleanedIncidentsAndOffenses(incidentTextTrimmed)
    return cleanedIncidentsAndOffenses

def getWarrantCodes(_rowText):
    try:
        # Each warrant can be found by spotting the warrantText and subtracting the code offset
        warrantText = ' Sedgwick County Warrant'
        warrantIndex = _rowText.index(warrantText)
        # Each warrant is 10 characters long
        warrantCodeOffset = warrantIndex - 10
        # Code lies before the warrantText
        warrantCode = _rowText[warrantCodeOffset:warrantIndex]
        # Recursion requires the warrantText to be removed from the _rowText
        trimmedText = _rowText.replace(warrantText, '', 1)
        yield warrantCode
        yield from getWarrantCodes(trimmedText)
    except ValueError:
        # Exits recursion when .index does not find a warrant
        pass

def getWarrantsFromRow(_rowText):
    return [code for code in getWarrantCodes(_rowText)]

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
                    getAddressFromRow(row),
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
                
