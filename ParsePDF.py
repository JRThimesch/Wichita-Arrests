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
        return min(i for i, item in enumerate(_list) if re.search(_pattern, item))
    else:
        return max(i for i, item in enumerate(_list) if re.search(_pattern, item))

def getRowStart(_list):
    pattern = '(\w+?)-(\w+?,)|(\w+?,)|JUVENILE'
    # All names (or starts to our lines) are listed at the end of the raw text given from the PDF, we can skip to the end by finding the 'Arrests:' index
    startIndex = _list.index("Arrests:") + 1
    _list = _list[startIndex:]

    matchElements = []

    for i in range(len(_list)):
        if re.match(pattern, _list[i]):
            matchElements.append(_list[i])
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

    return rows

def getNames(_list):
    pattern = '(\d{2}/\d{2}/\d{4})'
    dateIndex = regexFirstLast(_list, pattern)
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

def parseArrests(_list):
    pattern = '(\d{2}\w{1}\d{6})'

    _list = trimCharges(_list)
    
    for i in range(len(_list)):
        if re.search(pattern, _list[i][0]):
            _list = _list[:i]
            _list = trimCodes(_list)

            if len(_list) == 0:
                return None
            elif len(_list) == 1:
                return ' '.join(_list[0])
            else:
                newList = []
                for row in _list:
                    newList.append(' '.join(row))
                return '|'.join(newList)
        #else:
            #return 'EMPTY'

def parseIncidents(_list):
    incidentPattern = '(\d{2}\w{1}\d{6})'
    warrantPattern = '(\d{2}\w{2}\d{6})'

    _list = trimCharges(_list)
    
    for i in range(len(_list)):
        if re.search(warrantPattern, _list[i][0]):
            _list = _list[:i]
            break
    
    for i in range(len(_list)):
        if re.search(incidentPattern, _list[i][0]):
            _list = _list[i:]
            break

    _list = trimCodes(_list)

    if len(_list) == 0:
        return None
    elif len(_list) == 1:
        return ' '.join(_list[0])
    else:
        newList = []
        for row in _list:
            newList.append(' '.join(row))
        return '|'.join(newList)

def parseWarrants(_list):
    warrantPattern = '(\d{2}\w{2}\d{6})'

    _list = trimCharges(_list)

    for i in range(len(_list)):
        if re.search(warrantPattern, _list[i][0]):
            return len(_list[i:])

def trimCodes(_list):
    pattern = '(\d{3,})'
    for i, e in enumerate(_list):
        if '-' in _list[i]:
            _list[i] = _list[i][_list[i].index('-') + 1:]
        if '-' in _list[i] and re.search(pattern, _list[i][_list[i].index('-') - 1]):
            # Split the index and append the two new lists after deleting the original
            cutIndex = _list[i].index('-')
            str1 = _list[i][:cutIndex - 1]
            str2 = _list[i][cutIndex + 1:]
            del _list[i]
            _list.append(str1)
            _list.append(str2)
            trimCodes(_list)

    return _list

def expandAbbr(_list):
    print('ass')

if __name__ == "__main__":
    parsedText = getRawText('05-15-19 Arrest Report.pdf')

    rawTextFile = open("rawText.log", "w", encoding='utf-8')
    rawWordsFile = open("rawWords.log", "w", encoding='utf-8')

    toParse = ''.join(parsedText['content'])
    rawTextFile.write(toParse)

    names, birthdates, dates, ages, times, genders, addresses, arrests, incidents, warrants = [], [], [], [], [], [], [], [], [], []
    dataR, rows = [], []

    words = toParse.split()
    rawWordsFile.write(''.join(words))
    
    trimPageHeader(words)

    for s in reversed(trimRows(words)):
        #print(*s)
        #str1 = '||'.join(getNames(s))
        #str1 = '||'.join(getDates(s))
        #print(getNames(s) + getDates(s))
        names.append(getNames(s))
        dates.append(getDates(s))
        birthdates.append(getBirthdates(s))
        ages.append(getAges(s))
        times.append(getTimes(s))
        genders.append(getGenders(s))
        addresses.append(getAddresses(s))
        arrests.append(parseArrests(s))
        incidents.append(parseIncidents(s))
        warrants.append(parseWarrants(s))
        
    print(len(names))

    print('Name\t\tDate\t\tBirthdate\t\tAge\t\tTime\t\tGender\t\tAddress\t\tArrests\t\tIncidents\t\tWarrants')
    for i in range(len(names)):
        rows.append(names[i])
        rows.append(dates[i])
        rows.append(birthdates[i])
        rows.append(ages[i])
        rows.append(times[i])
        rows.append(genders[i])
        rows.append(addresses[i])
        rows.append(arrests[i])
        rows.append(incidents[i])
        rows.append(warrants[i])
        print(names[i], '\t\t', dates[i], '\t\t', birthdates[i], '\t\t', ages[i], '\t\t', times[i], '\t\t', genders[i], '\t\t', addresses[i], '\t\t', arrests[i], '\t\t', incidents[i], '\t\t', warrants[i])

    csv.register_dialect('dialect',
        delimiter = '|',
        quoting = csv.QUOTE_NONE,
        skipinitialspace = True)
    
    print(rows)


    with open('data.csv', 'w') as data:
        writer = csv.writer(data, dialect = 'dialect')
        #writer.writerows(rows)

    data.close()
    rawTextFile.close()
    rawWordsFile.close()