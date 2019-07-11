from tika import parser
import re, os, csv, sys, json

def getRawText(_pdf):
    return parser.from_file(_pdf)

def subfinder(_list, _pattern, _offset = 0):
    matchIndexes = []
    
    for i in range(len(_list)):
        if _list[i] == _pattern[0] and _list[i:i+len(_pattern)] == _pattern:
            matchIndexes.append(i + _offset)
    return matchIndexes

def trimPageHeader(_list):
    # Header patterns needed to find the indexes to be removed
    patternStart = ['Wichita', 'Police', 'Department']
    patternEnd = ['/', 'Warrants']
    
    startIndexList = subfinder(_list, patternStart)
    endIndexList = subfinder(_list, patternEnd, len(patternEnd))
    
    if len(startIndexList) is len(endIndexList):
        for i, k in reversed(list(enumerate(startIndexList))):
            del _list[startIndexList[i]:endIndexList[i]]

def violFix(_list):
    # VIOL is used to abbreviate VIOLENCE and VIOLATION which leads to problems when expanding abbreviations
    # This function alleviates that by finding instances where VIOLENCE should be inserted in place of VIOL
    for i, e in enumerate(_list):
        try:
            violIndex = e.index('VIOL')
            if e[violIndex - 1] == 'DOM':
                e[violIndex] = 'VIOLENCE'
        except ValueError:
            continue
    return _list

def isDate(_str):
    pattern = '(\d{2}/\d{2}/\d{4})'
    if re.search(pattern, _str):
        return True
    else:
        return False

def findLastOccurence(_list, _str):
    return max(i for i, item in enumerate(_list) if item == _str)

def findJuvenileStart(_list, _str):
    return max(i for i, item in enumerate(_list) if item == _str and isDate(_list[i + 1]))

def regexFronttoBack(_list, _pattern, _min = True):
    if _min:
        return min(i for i, element in enumerate(_list) if re.search(_pattern, element))
    else:
        return max(i for i, element in enumerate(_list) if re.search(_pattern, element))

def getRowStart(_str):
    # Separate by newlines
    splitText = toParse.splitlines()

    # All names (or starts to our lines) are listed at the end of the raw text given from the PDF, we can skip to the end by finding the index containing .rpt
    # For this, it's better to reverse the list so we can find the index sooner since it's toward the end of the file
    for e in reversed(splitText):
        if '.rpt' in e:
            startIndex = splitText.index(e)
            break

    # Create a new list for the lines that contain a comma or the word JUVENILE
    starters = [e for e in splitText[startIndex:] if ',' in e or 'JUVENILE' in e]

    # Remove the tabs from the lines
    for i, e in enumerate(starters):
        starters[i] = e.replace('\t', '')

    # Finally create a final list containing the strings that will be matched to the row starts
    rowStarters = []
    for e in starters:
        if e.find(',') is not -1:
            endIndex = e.index(',')
            rowStarters.append(e[:endIndex + 1].split(' ', 1)[0])
        if 'JUVENILE' in e:
            rowStarters.append('JUVENILE')
    
    return rowStarters

def trimEnd(_list):
    # startIndex needs to be one less to make sure we get the ##Total word out of the list
    startIndex = _list.index("Arrests:") - 1
    return _list[:startIndex]

def trimRows(_list):
    # First we need to get a list of rowStarters
    rowStarters = getRowStart(toParse)

    # Now we can trim the end of the document since we retrieved the rowStarters
    _list = trimEnd(_list)

    rows = []
    
    for word in reversed(rowStarters):

        # Using .index will find the first index but we need the last index in case there are duplicate rowStarters, which is likely
        if word == 'JUVENILE':
            lastIndex = findJuvenileStart(_list, word)
        else:
            lastIndex = findLastOccurence(_list, word)
        
        rows.append(_list[lastIndex:])

        # Trim down list with each word found
        _list = _list[:lastIndex]

    return rows[::-1]

def getFirstPart(_list):
    pattern = '(\d{2}:\d{2})'
    timeIndex = regexFronttoBack(_list, pattern)
    return _list[:timeIndex]

def getLastPart(_list):
    pattern = '(\d{2}:\d{2})'
    index = regexFronttoBack(_list, pattern) + 2
    return _list[index:]

def getNames(_list):
    # Finds the index of the date of birth and slices everything before it to get the name
    pattern = '(\d{2}/\d{2}/\d{4})'
    dobIndex = regexFronttoBack(_list, pattern)
    return ' '.join(_list[:dobIndex])

def getBirthdates(_list):
    pattern = '(\d{2}/\d{2}/\d{4})'
    dobIndex = regexFronttoBack(_list, pattern)
    return _list[dobIndex]

def getDates(_list):
    # Age and date are concatenated so we need to seperate the two with slicing
    pattern = '(\d{2}/\d{2}/\d{4})'
    dateIndex = regexFronttoBack(getFirstPart(_list), pattern, False)
    return _list[dateIndex][-10:]

def getAges(_list):
    # Age and date are concatenated so we need to seperate the two with slicing
    pattern = '(\d{2}/\d{2}/\d{4})'
    ageIndex = regexFronttoBack(getFirstPart(_list), pattern, False)
    return _list[ageIndex][:-10]

def getTimes(_list):
    pattern = '(\d{2}:\d{2})'
    timeIndex = regexFronttoBack(_list, pattern)
    return _list[timeIndex]

def getGenders(_list):
    # Returns the index after the time index
    pattern = '(\d{2}:\d{2})'
    genderIndex = regexFronttoBack(_list, pattern) + 1
    return expandGenders(_list[genderIndex])

def expandGenders(_str):
    replacements = {
        'W' : 'WHITE',
        'B' : 'BLACK',
        'A' : 'ASIAN',
        'I' : 'INDIAN',
        'H' : 'HISPANIC',
        'M' : 'MALE',
        'F' : 'FEMALE',
        'U' : 'UNKNOWN'
    }

    chars = list(_str)
    for i, char in enumerate(chars):
        if chars[i] in replacements:
            chars[i] = replacements[char]
        else:
            print('Unknown key:', chars[i])
    return ' '.join(chars)

def getAddresses(_list):
    pattern = '((0|8)\d{4,})|\d{6,}|(\d{4}\w+\d{2,}\w)'
    lastPart = getLastPart(_list)

    # For 'No address listed...'
    if 'No' in (lastPart):
        return ''
        
    arrestIndex = regexFronttoBack(lastPart, pattern)

    address = ' '.join(lastPart[:arrestIndex])
    if len(address) > 30:
        print('\nAbnormally large address:', address)
        print('\n\t', _list)
    return address

def countCharges(_list, _pattern):
    count = 0

    for i in range(len(_list)):
        if re.search(_pattern, _list[i]):
            count += 1
    
    return count

def trimCharges(_list):
    pattern = '(0\d{4,}|\d{6,})'
    
    _list = getLastPart(_list)

    try:
        arrestIndex = regexFronttoBack(_list, pattern)
    except:
        return None

    _list = _list[arrestIndex:]

    trimmed = []
    count = countCharges(_list, pattern)

    for j in range(count):
        startIndex = regexFronttoBack(_list, pattern, False)
        trimmed.append(_list[startIndex:])
            
        # Trim down list with each arrest found
        _list = _list[:startIndex]
        
    trimmed.reverse()
    return trimmed

def getIndices(_list, _word):
    return [i for i, element in enumerate(_list) if element == _word]

def parseArrests(_list):
    pattern = '(\d{2}\w{1,}\d{6})'
    
    if trimCharges(_list) is not None:
        _list = trimCharges(_list)
    else:
        return 'No data provided.'

    _list = violFix(_list)
    _list = spaceSlashes(_list)

    for i, e in enumerate(_list):
        if re.search(pattern, e[0]):
            _list = _list[:i]
            break
    
    if not _list:
        return None 
    else:
        _list = trimArrests(_list)
        _list = expandAbbreviations(_list)
        _list = expandPhrases(_list)
        

        if len(_list) == 1:
            return ' '.join(_list[0])
        else:
            return '+'.join([' '.join(row) for row in _list])

def parseIncidents(_list):
    incidentPattern = '(\d{2}\w{1}\d{6})'
    warrantPattern = '(\d{2}\w{2}\d{6})'

    if trimCharges(_list) is not None:
        _list = trimCharges(_list)
    else:
        return 'No data provided.'

    _list = violFix(_list)
    _list = spaceSlashes(_list)

    found = False
    
    for i, e in enumerate(_list):
        if re.search(warrantPattern, e[0]):
            _list = _list[:i]
            found = True
            break
    
    for i, e in enumerate(_list):
        if re.search(incidentPattern, e[0]):
            _list = _list[i:]
            found = True
            break

    if not found or not _list:
        return None

    _list = trimIncidents(_list)
    _list = expandAbbreviations(_list)
    _list = expandPhrases(_list)
    
    
    if len(_list) == 1:
        return ' '.join(_list[0])
    else:
        return '+'.join([' '.join(row) for row in _list])

def parseWarrants(_list):
    warrantPattern = '(\d{2}\w{2}\d{6})'

    if trimCharges(_list) is not None:
        _list = trimCharges(_list)
    else:
        return 'No data provided.'

    listOfWarrants = [e[0] for e in _list if re.search(warrantPattern, e[0])]

    if not listOfWarrants:
        return ''
    else:
        return '+'.join(listOfWarrants)

def trimArrests(_list):
    for i, e in enumerate(_list):
        for k in reversed(getIndices(e, '-')):
            cutIndex = k + 1
            codeIndex = k - 1

            if not e[codeIndex].isalpha():
                del e[codeIndex:cutIndex]
            else:
                del e[k]
                e[codeIndex] += ',' 

        if not e[0].isalpha():
            del e[0]
                
    return _list

def trimIncidents(_list):
    for i, e in enumerate(_list):
        for k in reversed(getIndices(e, '-')):
            cutIndex = k + 1
            codeIndex = k - 1
            if not e[codeIndex].isalpha():
                del e[codeIndex:cutIndex]
                e[codeIndex - 1] += '+' 
            else:
                del e[k]
                e[codeIndex] += ',' 
        
        if not e[0].isalpha():
            del e[0]

    return _list

def spaceSlashes(_list):
    slashPattern = '(\w{2,}).?\/(\w*)|(\D{2,})-(\D*)'
    for i, k in enumerate(_list):
        for j, word in enumerate(k):  
            if re.search(slashPattern, word):
                word = word.replace('/', ' / ')
                word = word.replace('-', ' - ')
                k[j] = word
    return _list
            
def expandAbbreviations(_list):
    for i, lofl in enumerate(_list):
        for j, element in enumerate(lofl):
            wordsList = str(element)
            wordsList = wordsList.split()
            for k, word in enumerate(wordsList):
                try:
                    wordsList[k] = abbreviations[word]
                except KeyError:
                    continue
            lofl[j] = ' '.join(wordsList)
        _list[i] = lofl
    return _list

def expandPhrases(_list):
    for i, sentence in enumerate(_list):
        sentenceStr = ' '.join(sentence)
        for phrase in phrases:
            sentenceStr = sentenceStr.replace(phrase, phrases[phrase])
        _list[i] = sentenceStr.split()
    return _list

def formatLines(_list):
    rows = []
    for i, k in enumerate(_list):
        rows.append([])
        rows[i].append(getNames(k))
        rows[i].append(getDates(k))
        rows[i].append(getBirthdates(k))
        rows[i].append(getAges(k))
        rows[i].append(getTimes(k))
        rows[i].append(getGenders(k))
        rows[i].append(getAddresses(k))
        rows[i].append(parseArrests(k))
        rows[i].append(parseIncidents(k))
        rows[i].append(parseWarrants(k))
        rows[i].append(getCensoredAddress(k))
        rows[i].append(getIdentifiers(rows[i][7], rows[i][9]))
    return rows

def getCensoredAddress(_list):
    address = getAddresses(_list)
    firstWord = address.split(' ', 1)[0]
    if firstWord.isnumeric():
        firstWord = firstWord[:-2] + 'XX'
        address = firstWord + ' ' + address.split(' ', 1)[1]

    try:
        apptIndex = address.index('#')
        address = address[:apptIndex - 1]
    except:
        pass

    return address

def removeNone(_list):
    for i, lofl in enumerate(_list):
        _list[i] = ['' if element is None else element for element in lofl]

def loadJSON(_file):
    with open(_file) as f:
        _dict = json.load(f)
    return _dict

def loadParsedFiles(_file):
    with open(_file) as f:
        print('Loading already parsed files...')
        _list = [line.replace('\n', '') for line in f]
        print('Parsed files loaded')

    return _list

def splitDates(_words):
    csv.register_dialect('dialect',
        delimiter = '|',
        quoting = csv.QUOTE_NONE,
        skipinitialspace = True)

    dates = list(set([l[1] for l in words]))
    dates.sort()
    for e in dates:
        toWrite = []
        fileCSV = 'CSVs/' + e.replace('/', '-') + '.csv'
        with open(fileCSV, 'w') as data:
            for l in _words:
                writer = csv.writer(data, dialect = 'dialect')
                if l[1] == e:
                    toWrite.append(l)
                        
            writer.writerows(toWrite)

def getIdentifiers(_arrests, _warrants):
    if _warrants and _arrests is None:
        return 'warrant'

    for key in identifiers:
        try:
            if _arrests.find(key) is not -1:
                return identifiers[key]
        except:
            pass

    return 'other'

def findAlreadyExisting(_path = '.'):
    files = os.listdir(_path)
    return[os.path.splitext(file)[0] for file in files if file.endswith('.pdf')]

if __name__ == "__main__":
    identifiers = loadJSON('identifiers.json')
    abbreviations = loadJSON('abbreviations.json')
    phrases = loadJSON('phrases.json')
    parsedFiles = loadParsedFiles('parsed.txt')
    neededFiles = findAlreadyExisting('PDFs/')

    for file in neededFiles:
        locationPDF = 'PDFs/'
        filePDF = locationPDF + file + '.pdf'
        
        if file in parsedFiles:
            if len(sys.argv) is 1 or sys.argv[1] is not 'r':
                print(file + '.pdf', 'already parsed!')
                continue
        
        print('Parsing', file + '.pdf...')

        parsedText = getRawText(filePDF)
        toParse = ''.join(parsedText['content'])

        with open('rawText.txt', "w", encoding='utf-8') as f:
            f.write(toParse)

        words = toParse.split()  

        trimPageHeader(words)
        words = trimRows(words)
        words = formatLines(words)
        removeNone(words)
        splitDates(words)

        with open('parsed.txt', 'a') as f:
            f.write(file)
            f.write("\n")