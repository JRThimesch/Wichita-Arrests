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

    # rowStarters = getRowStart(_list)

    pattern = '(\w*),'
    matchIndexes = []
    for i in range(len(_list)):
        if re.match(pattern,_list[i]):
            matchIndexes.append(i)
    
    return matchIndexes



if __name__ == "__main__":
    parsedText = getRawText('05-15-19 arrest Report.pdf')

    rawTextFile = open("rawText.log", "w", encoding='utf-8')
    rawWordsFile = open("rawWords.log", "w", encoding='utf-8')

    toParse = ''.join(parsedText['content'])
    words = toParse.split()

    

    trimPageHeader(words)
    #getRowStart(words)
    words = trimEnd(words)
    
    

    print(words)
    
    #print(trimRow(words))

    for i in trimRows(words):
        print(words[i])

    rawTextFile.write(toParse)
    rawWordsFile.write(''.join(words))

    rawTextFile.close()
    rawWordsFile.close()