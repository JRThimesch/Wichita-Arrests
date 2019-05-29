from tika import parser
import re
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
    else:
        print("EXCEPTION ERROR")

def findLastOccurence(_list, _str):
    return max(i for i, item in enumerate(_list) if item == _str)

def regexFirstLast(_list, _pattern, _min = True):
    if _min:
        return min(i for i, element in enumerate(_list) if re.search(_pattern, element))
    else:
        return max(i for i, element in enumerate(_list) if re.search(_pattern, element))

def getRowStart(_list):
    pattern = '(\d{2}:\d{2})'
    # All names (or starts to our lines) are listed at the end of the raw text given from the PDF, we can skip to the end by finding the 'Arrests:' index
    startIndex = _list.index("Arrests:") + 1
    _list = _list[startIndex:]

    matchElements = []

    for i in range(len(_list)):
        if re.match(pattern, _list[i]):
            matchElements.append(_list[i + 1])
            #print(_list[i])
    
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
        lastIndex = findLastOccurence(_list, word)

        rows.append(_list[lastIndex:])

        # Trim down list with each word found
        _list = _list[:lastIndex]

    return rows[::-1]

def getNames(_list):
    pattern = '(\d{2}/\d{2}/\d{4})'
    dateIndex = regexFirstLast(_list, pattern)
    #print(_list[:dateIndex])
    return ' '.join(_list[:dateIndex])

def getBirthdates(_list):
    pattern = '(\d{2}/\d{2}/\d{4})'
    dateIndex = regexFirstLast(_list, pattern)
    return _list[dateIndex]

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
    _list[genderIndex]
    return _list[genderIndex]

def getLastPart(_list):
    pattern = '(\d{2}:\d{2})'
    genderIndex = regexFirstLast(_list, pattern) + 2
    return _list[genderIndex:]

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
    
    for i in range(len(_list)):
        if re.search(pattern, _list[i][0]):
            _list = _list[:i]
            break
    
    if not _list:
        return None 
    else:
        _list = trimArrests(_list)
        print(_list)
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

    for i, e in enumerate(_list):
        if re.search(warrantPattern, e[0]):
            return i

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

def expandAbbr(_list):
    for i, lofl in enumerate(_list):
        #print(lofl)
        _list[i] = ['DOMESTIC VIOLENCE' if element is 'DV' else element for element in lofl]
    #return _list

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
    parsedText = getRawText('05-15-19 Arrest Report.pdf')

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

    print('Name Date Birthdate Age Time Gender Address Arrests Incidents Warrants')
    for i in words:
        print(*i)

    csv.register_dialect('dialect',
        delimiter = '|',
        quoting = csv.QUOTE_NONE,
        skipinitialspace = True)
    
    #print(words)

    with open('data.csv', 'w') as data:
        writer = csv.writer(data, dialect = 'dialect')
        writer.writerows(words)

    data.close()
    rawTextFile.close()
    rawWordsFile.close()