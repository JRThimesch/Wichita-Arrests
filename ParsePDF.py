from tika import parser
import re
import os
import recent
import csv

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

def regexFirstLast(_list, _pattern, _min = True):
    if _min:
        return min(i for i, element in enumerate(_list) if re.search(_pattern, element))
    else:
        return max(i for i, element in enumerate(_list) if re.search(_pattern, element))

def getRowStart(_list):
    pattern = '(\w*-?\w*,)|JUVENILE'
    # All names (or starts to our lines) are listed at the end of the raw text given from the PDF, we can skip to the end by finding the 'Arrests:' index
    startIndex = _list.index("Arrests:") + 1
    _list = _list[startIndex:]

    matchElements = []

    for i, e in enumerate(_list):
        if re.match(pattern, e):
            # This if statement fixes last names that have whitespaces in them.
            # Deincrement until one of these statements becomes true
            # Finds the index that the last name with whitespaces REALLY starts at
            while ',' not in _list[i - 2] and ',' not in _list[i - 3] and len(_list[i - 1]) is not 1 and not ':' in _list[i - 1]:
                i -= 1
            
            matchElements.append(_list[i])
    
    return matchElements

def trimEnd(_list):
    # startIndex needs to be one less to make sure we get the ##Total word out of the list
    startIndex = _list.index("Arrests:") - 1
    return _list[:startIndex]

def trimRows(_list):
    # First we need to get a list of rowStarters
    rowStarters = getRowStart(_list)

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

def getNames(_list):
    pattern = '(\d{2}/\d{2}/\d{4})'
    dateIndex = regexFirstLast(_list, pattern)
    return ' '.join(_list[:dateIndex])

def getBirthdates(_list):
    pattern = '(\d{2}/\d{2}/\d{4})'
    dobIndex = regexFirstLast(_list, pattern)
    return _list[dobIndex]

def getDates(_list):
    pattern = '(\d{2}/\d{2}/\d{4})'
    dateIndex = regexFirstLast(_list, pattern, False)
    return _list[dateIndex][-10:]

def getAges(_list):
    pattern = '(\d{2}/\d{2}/\d{4})'
    ageIndex = regexFirstLast(_list, pattern, False)
    return _list[ageIndex][:-10]

def getTimes(_list):
    pattern = '(\d{2}:\d{2})'
    timeIndex = regexFirstLast(_list, pattern)
    return _list[timeIndex]

def getGenders(_list):
    pattern = '(\d{2}:\d{2})'
    genderIndex = regexFirstLast(_list, pattern) + 1
    return expandGenders(_list[genderIndex])

def expandGenders(_str):
    replacements = {
        'W' : 'WHITE',
        'B' : 'BLACK',
        'A' : 'ASIAN',
        'I' : 'INDIAN',
        'H' : 'HISPANIC',
        'M' : 'MALE',
        'F' : 'FEMALE'
    }
    chars = list(_str)
    for i, char in enumerate(chars):
        chars[i] = replacements[char]
    return ' '.join(chars)

def getLastPart(_list):
    pattern = '(\d{2}:\d{2})'
    index = regexFirstLast(_list, pattern) + 2
    return _list[index:]

def getAddresses(_list):
    pattern = '(\d{6,})|(\d{4}\w+\d{2,}\w)|No'
    _list = getLastPart(_list)
    arrestIndex = regexFirstLast(_list, pattern)
    return ' '.join(_list[:arrestIndex])

def countCharges(_list, _pattern):
    count = 0

    for i in range(len(_list)):
        if re.search(_pattern, _list[i]):
            count += 1
    
    return count

def trimCharges(_list):
    pattern = '(\d{6,})'
    
    _list = getLastPart(_list)
    arrestIndex = regexFirstLast(_list, pattern)
    _list = _list[arrestIndex:]

    trimmed = []
    count = countCharges(_list, pattern)

    for j in range(count):
        startIndex = regexFirstLast(_list, pattern, False)
        trimmed.append(_list[startIndex:])
            
        # Trim down list with each arrest found
        _list = _list[:startIndex]
        
    trimmed.reverse()
    return trimmed

def getIndices(_list, _word):
    return [i for i, element in enumerate(_list) if element == _word]

def parseArrests(_list):
    pattern = '(\d{2}\w{1,}\d{6})'
    
    
    _list = trimCharges(_list)
    _list = violFix(_list)
    _list = spaceSlashes(_list)
    

    for i in range(len(_list)):
        if re.search(pattern, _list[i][0]):
            _list = _list[:i]
            break
    
    if not _list:
        return None 
    else:
        _list = expandAbbr(_list)
        _list = trimArrests(_list)
        
        #print(_list)
        if len(_list) == 1:
            return ' '.join(_list[0])
        else:
            newList = []
            for row in _list:
                newList.append(' '.join(row))
            return '+'.join(newList)

def parseIncidents(_list):
    incidentPattern = '(\d{2}\w{1}\d{6})'
    warrantPattern = '(\d{2}\w{2}\d{6})'

    _list = trimCharges(_list)
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

    _list = expandAbbr(_list)
    _list = trimIncidents(_list)
    
    if len(_list) == 1:
        return ' '.join(_list[0])
    else:
        newList = []
        for row in _list:
            newList.append(' '.join(row))
        return '+'.join(newList)

def parseWarrants(_list):
    warrantPattern = '(\d{2}\w{2}\d{6})'

    _list = trimCharges(_list)

    if not _list:
        return None

    count = 0
    for i, e in enumerate(_list):
        if re.search(warrantPattern, e[0]):
            count += 1
    return count

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
                e[codeIndex - 1] += ';' 
            else:
                del e[k]
                e[codeIndex] += ',' 
        
        if not e[0].isalpha():
            e[0] = 'INCIDENT #' + str(i + 1) + ':'

    return _list

def spaceSlashes(_list):
    slashPattern = '(\w{2,})\/(\w{2,})'
    for i, k in enumerate(_list):
        for j, word in enumerate(k):
            if re.search(slashPattern, word):
                k[j] = word.replace('/', ' / ')
    return _list
            
def expandAbbr(_list):
    abbr = {
        'DV' : 'DOMESTIC VIOLENCE',
        'VIOL' : 'VIOLATION',
        'SUSP' : 'SUSPENDED',
        'PROP' : 'PROPERTY',
        'POL' : 'POLICE'
    }

    for i, lofl in enumerate(_list):
        print(lofl)
        for j, element in enumerate(lofl):
            wordsList = str(element)
            wordsList = wordsList.split()
            for k, word in enumerate(wordsList):
                try:
                    wordsList[k] = abbr[word]
                    
                    print('MATCH:', word)
                except KeyError:
                    continue
            lofl[j] = ' '.join(wordsList)
        _list[i] = lofl
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
    return rows

def removeNone(_list):
    for i, lofl in enumerate(_list):
        _list[i] = ['-----' if element is None else element for element in lofl]

if __name__ == "__main__":

    neededFiles = recent.findAlreadyExisting('PDFs/', '.pdf')
    #existingFiles = recent.findAlreadyExisting('.csv')

    #print(neededFiles)
    #print(existingFiles)

    for file in neededFiles:
        locationCSV = 'CSVs/'
        locationPDF = 'PDFs/'
        fileCSV = locationCSV + file + '.csv'
        filePDF = locationPDF + file + '.pdf'
        
        if recent.doesExist(file, locationCSV):
            print(file + '.pdf', 'already parsed!')
            continue
        
        print('Parsing', file + '.pdf...')

        parsedText = getRawText(filePDF)

        rawTextFile = open("rawText.log", "w", encoding='utf-8')
        rawWordsFile = open("rawWords.log", "w", encoding='utf-8')

        toParse = ''.join(parsedText['content'])
                
        rawTextFile.write(toParse)

        words = toParse.split()
                
        rawWordsFile.write(''.join(words))
                
        trimPageHeader(words)
                
        words = trimRows(words)
                
        words = formatLines(words)
                
        removeNone(words)

            #print('Name Date Birthdate Age Time Gender Address Arrests Incidents Warrants')
            #for i in words:
                #print(*i)

        csv.register_dialect('dialect',
            delimiter = '|',
            quoting = csv.QUOTE_NONE,
            skipinitialspace = True)
                
                #print(words)

        with open(fileCSV, 'w') as data:
            writer = csv.writer(data, dialect = 'dialect')
            writer.writerows(words)

        data.close()
        rawTextFile.close()
        rawWordsFile.close()
