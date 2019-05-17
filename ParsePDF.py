from tika import parser
import re

def getRawText(_pdf):
    return parser.from_file(_pdf)

def subfinder(_list, _pattern, _offset = 0):
    matchIndexes = []
    for i in range(len(_list)):
        if _list[i] == _pattern[0] and _list[i:i+len(_pattern)] == _pattern:
            matchIndexes.append(i + _offset)
    return matchIndexes

def trimPageHeader(_list):
    #Header patterns needed to find the indexes to be removed
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
    return max(loc for loc, val in enumerate(_list) if val == _str)

def regexFirstLast(_list, _pattern, _min = True):
    if _min:
        return min(i for i, item in enumerate(_list) if re.search(_pattern, item))
    else:
        return max(i for i, item in enumerate(_list) if re.search(_pattern, item))

def getRowStart(_list):
    pattern = '(\d{2}:\d{2})'
    # All names (or starts to our lines) are listed at the end of the raw text given from the PDF, we can skip to the end by finding the 'Arrests:' index
    startIndex = _list.index("Arrests:") + 1
    matchElements = []

    newList = _list[startIndex:]

    for i in range(len(newList)):
        if re.match(pattern, newList[i]):
            # Add one to get to the name that starts a row in the PDF
            matchElements.append(newList[i + 1])
    
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
    #print(findFirstOccurence(_list, pattern))

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

if __name__ == "__main__":
    parsedText = getRawText('05-15-19 arrest Report.pdf')

    rawTextFile = open("rawText.log", "w", encoding='utf-8')
    rawWordsFile = open("rawWords.log", "w", encoding='utf-8')

    toParse = ''.join(parsedText['content'])
    rawTextFile.write(toParse)

    names, birthdates, dates, ages, times, genders = [], [], [], [], [], []

    words = toParse.split()
    rawWordsFile.write(''.join(words))
    
    trimPageHeader(words)

    for s in reversed(trimRows(words)):
        print(*s)
        names.append(getNames(s))
        birthdates.append(getBirthdates(s))
        dates.append(getDates(s))
        ages.append(getAges(s))
        times.append(getTimes(s))
        genders.append(getGenders(s))
        print('ass', getLastPart(s))

    print('Name\t\tDate\t\tBirthdate\t\tAge\t\tTime\t\tGender')
    for i in range(len(names)):
        print(names[i], '\t\t', dates[i], '\t\t', birthdates[i], '\t\t', ages[i], '\t\t', times[i], '\t\t', genders[i])
    #print(birthdates)
    #print(dates)
    #print(ages)

    rawTextFile.close()
    rawWordsFile.close()
    #print(trimRow(words))

    #for i in trimRows(words):
        #print(words[i])


    