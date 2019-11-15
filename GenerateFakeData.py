import pandas as pd
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

stemmer = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')

def getStemmedAndTokenizedArrest(_arrest):
    _arrest = _arrest.lower().replace(':', '').replace('/', ' ')
    _arrest = _arrest.replace(',', '').replace("'", '')
    
    # Remove numbers from arrest if they exist
    if not _arrest.replace(' ', '').isalpha():
        _arrest = ''.join([i for i in _arrest if not i.isdigit()])

    tokens = tokenizer.tokenize(_arrest)
    filteredWords = filter(lambda token: token not in stopwords.words('english'), tokens)
    stemmedArrest = map(stemmer.stem, filteredWords)
    tokenizedAndStemmedArrest = ' '.join(stemmedArrest)
    return tokenizedAndStemmedArrest

def getFakeDataFromList(_listOfFakeCharges):
    fakeArrests = [fake.partition('|')[0] for fake in _listOfFakeCharges]
    fakeTags = [fake.partition('|')[2] for fake in _listOfFakeCharges]
    fakeStems = [getStemmedAndTokenizedArrest(arrest) for arrest in fakeArrests]

    dataDict = {'arrests' : fakeArrests, 'tags' : fakeTags, 'stems' : fakeStems}

    fakeData = pd.DataFrame(data=dataDict)
    fakeData.to_csv('data/fakeData.csv', sep = '|')

if __name__ == "__main__":
    with open('data/fakeCharges.txt', 'r') as f:
        fakeCharges = f.read().split('\n')

    getFakeDataFromList(fakeCharges)

