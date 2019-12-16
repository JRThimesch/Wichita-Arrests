import os
import pandas as pd
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

stemmer = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')

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
        tags += [tag.strip("'") for tag in listOfTags if tag != "'Warrants'"]
    return tags

def getStemmedAndTokenizedArrest(_arrest):
    _arrest = _arrest.lower().replace(':', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ')
    _arrest = _arrest.replace(',', ' ').replace("'", '').replace(';', ' ')
    
    # Remove numbers from arrest if they exist
    if not _arrest.replace(' ', '').isalpha():
        _arrest = ''.join([i for i in _arrest if not i.isdigit()])

    tokens = tokenizer.tokenize(_arrest)
    filteredWords = filter(lambda token: token not in stopwords.words('english'), tokens)
    stemmedArrest = map(stemmer.stem, filteredWords)
    tokenizedAndStemmedArrest = ' '.join(stemmedArrest)
    return tokenizedAndStemmedArrest

def getTrueDataFromDataFrame(_df):
    arrestsFull = _df['Arrests']
    tagsFull = _df['Tags']

    print(arrestsFull.shape, tagsFull.shape)

    arrests = getArrestsFromColumn(arrestsFull)
    tags = getTagsFromColumn(tagsFull)
    stems = [getStemmedAndTokenizedArrest(arrest) for arrest in arrests]

    dataDict = {'arrests' : arrests, 'tags' : tags, 'stems' : stems}
    
    trueData = pd.DataFrame(data=dataDict)
    trueData.to_csv('data/trueData.csv', sep = '|')

    return trueData

if __name__ == "__main__":
    CSVs = getCSVs('CSVs/')
    dfFull = getFullDataFrame(CSVs)
    getTrueDataFromDataFrame(dfFull)