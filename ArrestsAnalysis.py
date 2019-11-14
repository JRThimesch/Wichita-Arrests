import os
import pandas as pd
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

def getCSVs(_path):
    files = os.listdir(_path)
    return [_path + file for file in files if file.endswith('.csv')]

def getFullDataFrame(_CSVs):
    strToList = lambda x: x.strip("[]").replace("\"", "'").split("', ")
    conversionDict = {"Arrests" : strToList,
        "Tags" : strToList}
    fullDataframe = pd.DataFrame(data=[])
    for csv in _CSVs:
        print('Opening...', csv)
        dfCSV = pd.read_csv(csv, sep='|', index_col=0, converters=conversionDict)
        fullDataframe = fullDataframe.append(dfCSV, ignore_index=True)
    return fullDataframe

def getArrestsFromColumn(_column):
    arrests = []
    for listOfArrests in _column:
        for arrest in listOfArrests:
            arrest = arrest.strip("'")
            if arrest != "No arrests listed.":
                arrests.append(arrest)
    return arrests

def getTagsFromColumn(_column):
    tags = []
    for listOfTags in _column:
        tags += [tag.strip("'") for tag in listOfTags if tag]
    return tags

def getStemmedAndTokenizedArrest(_arrest):
    stemmer = PorterStemmer()
    tokenizer = RegexpTokenizer(r'\w+')

    _arrest = _arrest.lower()
    _arrest = _arrest.replace(':', '')
    _arrest = _arrest.replace('/', ' ')

    tokens = tokenizer.tokenize(_arrest)
    filteredWords = filter(lambda token: token not in stopwords.words('english'), tokens)
    stemmedArrest = map(stemmer.stem, filteredWords)
    tokenizedAndStemmedArrest = ' '.join(stemmedArrest)
    return tokenizedAndStemmedArrest

if __name__ == "__main__":
    CSVs = getCSVs('CSVs/')
    
    dfFull = getFullDataFrame(CSVs)
    arrestsFull = dfFull['Arrests']
    tagsFull = dfFull['Tags']

    arrests = getArrestsFromColumn(arrestsFull)
    tags = getTagsFromColumn(tagsFull)
    stemmedArrests = map(getStemmedAndTokenizedArrest, arrests)

    dataDict = {'arrests' : arrests, 'tags' : tags, 'stemmed' : stemmedArrests}
    
    trainingData = pd.DataFrame(data=dataDict)
    trainingData.to_csv('data/tagData.csv', sep = '|')
    print(trainingData)