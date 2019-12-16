import pandas as pd
import json
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

stemmer = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')

def loadJSON(_file):
    with open(_file, encoding='utf-8') as f:
        _dict = json.load(f)
    return _dict

def getStemmedAndTokenizedArrest(_arrest):
    _arrest = _arrest.lower().replace(':', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ')
    _arrest = _arrest.replace(',', ' ').replace("'", '').replace(";", " ")
    
    # Remove numbers from arrest if they exist
    if not _arrest.replace(' ', '').isalpha():
        _arrest = ''.join([i for i in _arrest if not i.isdigit()])

    tokens = tokenizer.tokenize(_arrest)
    filteredWords = filter(lambda token: token not in stopwords.words('english'), tokens)
    stemmedArrest = map(stemmer.stem, filteredWords)
    tokenizedAndStemmedArrest = ' '.join(stemmedArrest)
    return tokenizedAndStemmedArrest

def getDataFrameFromJSON(_json):
    df = pd.DataFrame()

    for key in _json:
        for paragraph in _json[key]:
            stem = getStemmedAndTokenizedArrest(paragraph)
            df = df.append({"tags": key, "text": paragraph, "stems": stem}, ignore_index=True)

    return df

if __name__ == "__main__":
    lawDataJSON = loadJSON('data/lawData.json')
    lawData = getDataFrameFromJSON(lawDataJSON)
    lawData.to_csv('data/lawData.csv', sep = '|')