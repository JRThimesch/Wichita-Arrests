import PyPDF2
import os, re, json, logging, nltk
import pandas as pd
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

HEADER_STR = 'Incidents with Offenses / Warrants'
HEADER_OFFSET = len('Incidents with Offenses / Warrants')
logging.basicConfig(level=logging.INFO, filename='runtime.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
pd.set_option('display.max_rows', 1000)
lancaster = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')

def loadJSON(_file):
    with open(_file) as f:
        _dict = json.load(f)
    return _dict

def getPDFs(_path):
    files = os.listdir(_path)
    return [_path + file for file in files if file.endswith('.pdf')]

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
    return re.findall(_pattern, _str)[n]

def regexTrimLeftOrRight(_pattern, _str, _left = True):
    try:
        matchIndex = re.search(_pattern, _str).start()
        if _left:
            _str = _str[matchIndex:]
        else:
            _str = _str[:matchIndex]
    except AttributeError:
        pass
    return _str

def regexSplitAndTrim(_pattern, _str):
    listSplit = re.split(_pattern, _str)
    listSplitAndTrimmed = list(filter(None, listSplit))
    return listSplitAndTrimmed

def getExpandedGenderInfo(_abbreviation):
    replacements = {
        'W' : 'WHITE',
        'B' : 'BLACK',
        'A' : 'ASIAN',
        'H' : 'HISPANIC',
        'I' : 'INDIAN',
        'M' : 'MALE ',
        'F' : 'FEMALE ',
        'U' : 'UNKNOWN'
    }

    try:
        abbreviationList = [replacements[char] for char in _abbreviation]
        return ' '.join(abbreviationList)
    except KeyError:
        raise RuntimeError

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
    _fullText = _fullText.replace(' +', '+')
    _fullText = findRaceGender(_fullText)

    return ' '.join(_fullText.split())

def getNumOfCharUntilNumber(_str):
    # Returns the index of the last non-digit character
    for i, char in enumerate(_str):
        if not char.isdigit():
            continue
        return i

def getLastJuvenileIndex(_fullText):
    # The purpose of this function is to recurse until a valid row is found
    # This is done by checking for a date after a found JUVENILE word
    # The chance of a date validly occurring in arrests/incidents is incredibly low
    juvenileIndex = _fullText.rindex('JUVENILE')
    # 9 is the length of JUVENILE plus 1 for a space char
    juvenileIndexOffset = juvenileIndex + 9
    # 10 is the length of a valid date
    potentialDateIndex = juvenileIndexOffset + 10
    potentialDate = _fullText[juvenileIndexOffset:potentialDateIndex]

    if potentialDate.count('/') == 2:
        # Exit recursion when a valid date is found
        return juvenileIndex
    
    # Trims out JUVENILE if it is not a row starter
    newText = _fullText[:juvenileIndex]
    return getLastJuvenileIndex(newText)

def getLastJuvenileRow(_fullText):
    juvenileRow = _fullText[getLastJuvenileIndex(_fullText):]
    return juvenileRow

def getRowBeforeEmpty(_fullText):
    # Dates occur only once per record, making them useful for finding a new record
    # By finding the last time and subtracting an offset for the date, the empty name can be fixed
    lastTime = regexFindNth('(\d{2}:\d{2})', _fullText, -1)
    lastTimeIndex = _fullText.index(lastTime)
    fixedRowIndex = lastTimeIndex - 11
    return _fullText[fixedRowIndex:]

def splitRows(_fullText, _nameArray):
    try:
        currentName = _nameArray.pop().strip()
        if currentName:
            if currentName == 'JUVENILE':
                # Juveniles have high tendency to cause issues
                # This is due to the word JUVENILE being contained in arrests and incidents
                currentRow = getLastJuvenileRow(_fullText)
            else:
                # Unique names can be partitioned out from the end
                currentRowPartitioned = _fullText.rpartition(currentName)
                currentRow = currentRowPartitioned[1] + currentRowPartitioned[2]
            
            # Replace the row from the text instead of slicing
            _fullText = _fullText.replace(currentRow, '', 1)
            yield currentRow.strip()
        else:
            # If the name is None, then the row needs to be fixed
            yield 'No name listed. ' + getRowBeforeEmpty(_fullText)
        yield from splitRows(_fullText, _nameArray)
    except IndexError:
        pass

def getNamesFromRow(_rowText):
    # First digit signals the beginning of the date, ergo, the end of the name entry
    sliceIndex = getNumOfCharUntilNumber(_rowText)
    name = _rowText[:sliceIndex]
    return name

def isBirthdateFound(_trimmedRowText):
    # Ideally, the row gets trimmed into a {birthdate} {age} {date} format
    # Otherwise it is trimmed into a {birthdate} {age} {gibberish} or just a {date} format
    # So if there is more than just a date, the birthdate is found otherwise it is not
    lenOfTrimmedRow = len(_trimmedRowText)
    if lenOfTrimmedRow == 10:
        return False
    else:
        return True

def getTrimmedRowForDateAndBirthdate(_rowText):
    # Trims the row into a {birthdate} {age} {date} format
    trimNameIndex = getNumOfCharUntilNumber(_rowText)
    trimmedRowAtName = _rowText[trimNameIndex:]
    remainingTimeCharOffset = -3
    trimmedRowAtTime = trimmedRowAtName.partition(':')[0][:remainingTimeCharOffset]
    return trimmedRowAtTime

def isValidDate(_date):
    # When the time is missing, the date comes out incorrectly
    numOfSlashes = _date.count('/')
    if numOfSlashes == 2:
        return True
    return False

def getDateFromRow(_rowText):
    trimmedRow = getTrimmedRowForDateAndBirthdate(_rowText)
    if isBirthdateFound(trimmedRow):
        date = trimmedRow.rpartition(' ')[2]
        if not isValidDate(date):
            return 'No date found.'
    else:
        date = trimmedRow.partition(' ')[0]
    return date

def getBirthdateFromRow(_rowText):
    trimmedRow = getTrimmedRowForDateAndBirthdate(_rowText)
    if isBirthdateFound(trimmedRow):
        birthdate = trimmedRow.partition(' ')[0]
    else:
        birthdate = 'No birthdate found.'
    return birthdate

def getAgeFromRow(_rowText):
    try:
        agePattern = ('\d{2}\/\d{2}\/\d{4}(.+?)\d{2}\/\d{2}\/\d{4}')
        age = re.search(agePattern, _rowText).group(1)
        return age.strip()
    except AttributeError:
        return 'No age found.'
    
def getExpandedRaceGenderInfoFromException(_rowText):
    trimmedRowText = _rowText.partition('No address listed...')[0]
    trimmedRowText = trimmedRowText.rpartition(' ')[2]
    raceGenderInfo = ''.join(filter(lambda i: i.isalpha(), trimmedRowText))
    if not raceGenderInfo or len(raceGenderInfo) > 3:
        raise RuntimeError('UNUSUAL FORMATTING FOUND, REGEX FAILED, ALTERNATE SOLUTION FAILED')
    expandedRaceGenderInfo = getExpandedGenderInfo(raceGenderInfo).strip()
    return expandedRaceGenderInfo.rpartition(' ')

def getSexFromExceptionRow(_rowText):
    sex = getExpandedRaceGenderInfoFromException(_rowText)[2]
    return sex

def getRaceFromExceptionRow(_rowText):
    race = getExpandedRaceGenderInfoFromException(_rowText)[0]
    return race

def getRaceFromRow(_rowText):
    try:
        racePattern = '\d{2}:\d{2}(.+?)' + getSexFromRow(_rowText)
        race = re.search(racePattern, _rowText).group(1)
        return race.strip()
    except:
        logging.warning('Race not found in row text: \n\t' + _rowText)
        logging.warning('Deferring to alternate solution')
        return getRaceFromExceptionRow(_rowText)

def getSexFromRow(_rowText):
    if 'FEMALE' in _rowText:
        return 'FEMALE'
    elif 'MALE' in _rowText:
        return 'MALE'
    else:
        logging.warning('Sex not found in row text: \n\t' + _rowText)
        logging.warning('Deferring to alternate solution')
        return getSexFromExceptionRow(_rowText)

def getTimeFromRow(_rowText):
    try:
        timePattern = '(\d{2}:\d{2})'
        return re.search(timePattern, _rowText).group(1)
    except:
        logging.warning('Time not found in row text: \n\t' + _rowText)
        return 'No time found.'

def getTrimmedAddressText(_rowText):
    # Get as close to the actual address as possible
    address = _rowText.rpartition('MALE')[2]
    address = address.partition('-')[0]
    address = address.partition('#')[0]
    address = address.partition('No')[0]
    address = address.partition('Sedgwick')[0]
    return address.strip()  

def getHighwayAddress(_address, _highways):
    for highway in _highways:
        partitionedAddress = _address.partition(highway)
        _address =  partitionedAddress[0] + partitionedAddress[1]
    return _address.strip()

def findHighwaysInAddress(_address):
    # The only highways that appear are in the tuple 'highways'
    # If a highway is in the address, the address will get trimmed down to match it
    highways = ('I 135', 'K 96', 'I 235')
    if any(highway in _address for highway in highways):
        return getHighwayAddress(_address, highways)
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
        trimmedWordLenOffset = getNumOfCharUntilNumber(lastWordInAddress)
        trimIndex = lastWordInAddressIndex + trimmedWordLenOffset
        trimmedAddress = _addressText[:trimIndex]
    except:
        # Exception occurs when the address does NOT contain incorrectly concatenated info
        # However, sometime numbers remain at the end that aren't needed, so they're trimmed
        removeTrailingNumbersAndCodesFromList(addressTextList)
        trimmedAddress = ' '.join(addressTextList)

    return trimmedAddress

def getAddressFromRow(_rowText):
    if 'No address listed...' in _rowText:
        return 'No address listed.'
    addressText = getTrimmedAddressText(_rowText)        
    # Typically addresses do not end in numbers, however, highways do
    # There is no way to differentiate an address ending number from an arrest code
    # Therefore, the easiest solution is to look for those highways before continuing on
    highwayAddressFound = findHighwaysInAddress(addressText)
    if highwayAddressFound:
        return highwayAddressFound

    trimmedAddress = getTrimmedAddress(addressText)
    return trimmedAddress.strip()

def getTrimmedArrestsText(_rowText):
    # Get as close to the actual arrests as possible
    arrests = _rowText.rpartition('MALE')[2]
    arrests = arrests.partition('Sedgwick')[0]

    if ' - ' in arrests:
        arrests = arrests.partition(' - ')[2]
    else:
        return ''
    return arrests.strip()

def getSplitArrests(_trimmedRowText):
    splitPattern = '\d+\w?\s?.{1,2}?\w?\s-\s'
    splitArrests = re.split(splitPattern, _trimmedRowText)
    return splitArrests

def removeTrailingNumbersFromArrest(_arrestLastWord):
    # The last word of almost every arrest has some kind of arrest codes concatenated to it
    trimIndex = getNumOfCharUntilNumber(_arrestLastWord)
    return _arrestLastWord[:trimIndex]

def isValidArrestAbbreviation(_arrestLastWord):
    # Sometimes the splitting does not work 100%
    # So far, 'DM' gets left over from codes that use it
    # This can be expanded in the future if new problems arise
    invalidLastWords = ['DM']
    return _arrestLastWord not in invalidLastWords

def isLastWordValid(_arrestLastWord):
    # If the lastWord is one char long: return False
    # If the lastWord is not a valid abbreviation: return False
    # All words are valid otherwise
    lenOfLastWord = len(_arrestLastWord)
    return lenOfLastWord != 1 and isValidArrestAbbreviation(_arrestLastWord)

def getLastWordFromArrest(_arrest):
    partitionedArrest = _arrest.strip().rpartition(' ')
    lastWord = partitionedArrest[2]
    if not isLastWordValid(lastWord):
        # Go to the word before the lastWord in the given recursion and test it's validity
        restOfArrest = partitionedArrest[0]
        return getLastWordFromArrest(restOfArrest)
    return lastWord

def getFixedPlusSignInArrest(_arrest):
    # Easiest way to fix plus signs concatenated with arrest codes is to just partition
    partitionedArrest = _arrest.partition('+')
    beforePlus = partitionedArrest[0] + partitionedArrest[1]
    return beforePlus

def removeParenthesesContent(_arrest):
    # Some arrests have content within parentheses that adds no extra info
    parenthPattern = '\(.+?\)'
    _arrest = re.sub(parenthPattern, '', _arrest)
    return _arrest.strip()

def getRegexReplacements(_arrest):
    # Uses abbreviations.json to correct abbreviations
    # Must use the whole word tag (\b), otherwise it is no better than .replace
    for key in abbreviations:
        if key not in _arrest:
            continue
        keyPattern = '\\b' + key + '\\b'
        _arrest = re.sub(keyPattern, abbreviations[key], _arrest)
    return _arrest

def getReplacementWords(_arrest):
    # Uses replacements.json to correct formatting
    # It is also useful to generalize some arrests
    for key in replacements:
        if key not in _arrest:
            continue
        _arrest = _arrest.replace(key, replacements[key])
    return _arrest

def getFormattedArrest(_arrest):
    logging.info('Original Arrest:\t' + _arrest)
    if '(' in _arrest:
        _arrest = removeParenthesesContent(_arrest)
    if ' EFF' in _arrest:
        # Superfluous info that can be removed
        _arrest = _arrest.rpartition(' EFF')[0]
    _arrest = getReplacementWords(_arrest)
    _arrest = getRegexReplacements(_arrest)
    logging.info('New Arrest:\t' + _arrest)
    return _arrest

def getTrimmedAndFormattedArrestsList(_listOfArrests):
    for arrest in _listOfArrests:
        lastWord = getLastWordFromArrest(arrest)
        if '+' in lastWord:
            # Plus signs get concatenated incorrectly and need to defer to the function
            arrest = getFixedPlusSignInArrest(arrest)
            yield getFormattedArrest(arrest)
            continue
        if lastWord.isalpha():
            # No arrest codes in the arrest; the arrest is perfectly split
            yield getFormattedArrest(arrest)
            continue
        newLastWord = removeTrailingNumbersFromArrest(lastWord)
        correctPartOfArrest = arrest.rpartition(lastWord)[0]
        # Cannot use .replace here because of the recursion for finding the lastWord
        # If the function recurses, then the failed lastWords would remain at the end of the arrest
        arrest = correctPartOfArrest + newLastWord
        yield getFormattedArrest(arrest)

def getArrestsFromRow(_rowText):
    incidentIdPattern = '\s?\d{2}C\d{6,}\ss\d{3,}\s-\s|\s?\d{2}C\d{6}\s?'
    warrantPattern = '\d{2}[A-Z]{2}\d{6}'
    trimmedIncidents = regexTrimLeftOrRight(incidentIdPattern, _rowText, False)
    trimmedWarrantsAndIncidents = regexTrimLeftOrRight(warrantPattern, trimmedIncidents, False)
    trimmedRowText = getTrimmedArrestsText(trimmedWarrantsAndIncidents)
    if not trimmedRowText:
        return ['No arrests listed.']
    listOfArrests = getSplitArrests(trimmedRowText)
    trimmedAndFormattedListOfArrests = [e.strip() for e in getTrimmedAndFormattedArrestsList(listOfArrests)]
    return trimmedAndFormattedListOfArrests
    
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

def validateDates(_dataframe):
    # In incredibly rare cases, the date is missing
    # So this counts the number of missing dates and selects the nearest date in the PDF
    # Usually, the noDatesCount will be 0
    noDatesCount = (_dataframe['Date'] == 'No date found.').sum()
    if not noDatesCount:
        return _dataframe
    # Nearest date is ideally the one right after the missing date entries, so choose that
    defaultReplaceDate = _dataframe['Date'][noDatesCount]
    _dataframe['Date'] = _dataframe['Date'].replace('No date found.', defaultReplaceDate)
    return _dataframe

def logProblemWithPDF(_pdf, _exception):
    logging.critical('PROBLEM FOUND FOR ' + _pdf)
    logging.exception(_exception)
    logging.critical('EXITING FOR ' + _pdf)

def getSeparatedArrests(_dataframe):
    listOfArrests = _dataframe['Arrests'].tolist()
    for arrests in listOfArrests:
        for arrest in arrests:
            yield arrest

def getStemmedAndTokenizedArrest(_arrest):
    _arrest = _arrest.lower()
    _arrest = _arrest.replace(':', '')
    _arrest = _arrest.replace('/', ' ')
    tokens = tokenizer.tokenize(_arrest)
    filteredWords = filter(lambda token: token not in stopwords.words('english'), tokens)
    stemmedArrest = [lancaster.stem(word) for word in filteredWords]
    tokenizedAndStemmedArrest = ' '.join(stemmedArrest)
    return tokenizedAndStemmedArrest

def matchWholeArrest(_arrestToMatch):
    try:
        return tagsWholeArrestsDict[_arrestToMatch]
    except KeyError:
        return matchPhrases(_arrestToMatch)

def matchPhrases(_arrestToMatch):
    for key in tagsPhrasesDict:
        if key in _arrestToMatch:
            return tagsPhrasesDict[key]
    return matchSingular(_arrestToMatch)

def matchSingular(_arrestToMatch):
    for key in tagsSingularDict:
        if key in _arrestToMatch:
            return tagsSingularDict[key]
    print(_arrestToMatch)
    return None

def getTagsFromArrests(_arrestsList):
    if _arrestsList == ['No arrests listed.']:
        return None
    stemmedAndTokenizedArrests = [getStemmedAndTokenizedArrest(arrest) for arrest in _arrestsList]
    return [matchWholeArrest(arrest) for arrest in stemmedAndTokenizedArrests]

if __name__ == "__main__":
    arrestsSeries = pd.Series(data=[])
    abbreviations = loadJSON('JSONS/regexAbbreviations.json')
    replacements = loadJSON('JSONS/replacements.json')
    tagsSingularDict = loadJSON('JSONS/tagsSingular.json')
    tagsWholeArrestsDict = loadJSON('JSONS/tagsWholeArrests.json')
    tagsPhrasesDict = loadJSON('JSONS/tagsPhrases.json')
    for pdf in getPDFs('PDFs/'):
        try:
            logging.info('Parsing... %s', pdf)
            print('Parsing...', pdf)

            pdfObject = openPDF(pdf)
            nameArray = getNamesFromPDF(pdfObject)
            fullText = combinePages(pdfObject)
            fullTextSpaced = fixFullTextSpacing(fullText)
            rowsAsList = []
            
            for row in splitRows(fullTextSpaced, nameArray):
                logging.info(row)
                arrests = getArrestsFromRow(row)
                rowsAsList.append([
                    getNamesFromRow(row),
                    getBirthdateFromRow(row),
                    getAgeFromRow(row),
                    getRaceFromRow(row),
                    getSexFromRow(row),
                    getDateFromRow(row),
                    getTimeFromRow(row),
                    getAddressFromRow(row),
                    arrests,
                    getIncidentsFromRow(row),
                    getWarrantsFromRow(row),
                    None,
                    getTagsFromArrests(arrests)
                ])

            # Because of the algorithm, the list needs to be reversed for the correct order
            rowsAsList.reverse()
            
            df = pd.DataFrame(data=rowsAsList, columns=[
                'Name', 'Birthdate', 'Age', 
                'Race', 'Sex', 'Date', 'Time', 
                'Address', 'Arrests', 'Incidents', 
                'Warrants', 'Category', 'Tags' 
            ])

            df = validateDates(df)

            #print(df)

            separatedArrests = [e for e in getSeparatedArrests(df)]
            arrestsSeries = arrestsSeries.append(pd.Series(separatedArrests))
        except RuntimeError as e:
            logProblemWithPDF(pdf, e)
            continue
    counts = arrestsSeries.value_counts().sort_index()
    counts.to_string(buf='arrests.txt')

    tags = getTagsFromArrests(arrestsSeries.tolist())
    uniqueArrests = pd.Series(arrestsSeries.unique()).tolist()
    uniqueTags = getTagsFromArrests(uniqueArrests)
    learningData = pd.Series(data=uniqueTags, index=uniqueArrests).sort_index()
    print(learningData)
    learningDataCounts = pd.DataFrame(data =learningData.value_counts().sort_index(), columns = ['tag'])
    learningDataCounts['count'] = 0
    for index, val in learningDataCounts.iterrows():
        learningDataCounts.loc[index, 'count'] = tags.count(index)
    print(learningDataCounts)