import pandas as pd
import numpy as np
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

stemmer = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')
vectorizer = TfidfVectorizer()
encoder = LabelEncoder()
np.set_printoptions(threshold=sys.maxsize)

def getSVCParameters(_x_train, _y_train):
    C = [0.01, 0.1, 1, 10, 100]
    gamma = [0.001, 0.01, 0.1, 1, 10]
    degrees = [2, 4, 6]
    # Parameters defined in the homework
    param_grid = {'C': C, 'degree' : degrees, 'gamma' : gamma}
    gridSearch = GridSearchCV(SVC(), param_grid, cv=3)
    gridSearch.fit(_x_train, _y_train)

    # Modified from StackOverflow
    means = gridSearch.cv_results_['mean_test_score']
    stds = gridSearch.cv_results_['std_test_score']
    for mean, params in zip(means, gridSearch.cv_results_['params']):
            print("%0.5f for %r" % (mean, params))

    return gridSearch.best_params_
    
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

def getSplitAndEncodedData(_x, _y):
    x_train, x_test, y_train, y_test = train_test_split(x, y, 
        test_size=0.3, random_state=133)

    x_train_vect = vectorizer.transform(x_train)
    x_test_vect = vectorizer.transform(x_test)
    y_train_enc = encoder.transform(y_train)
    y_test_enc = encoder.transform(y_test)

    return x_train_vect, x_test_vect, y_train_enc, y_test_enc

if __name__ == "__main__":
    trueData = pd.read_csv('data/trueData.csv', sep='|')
    fakeData = pd.read_csv('data/fakeData.csv', sep='|')

    combinedData = trueData.append(fakeData).append(fakeData)

    x = combinedData['stems']
    y = combinedData['tags']

    vectorizer.fit(x)
    encoder.fit(y)

    newArrests = [
        'threaten', 'entering wrong way', 'entering after hours', 'possession weapons',
        'school bus sign', 'destruction of personal property: vehicle', 'grand theft auto',
        'broken head lamp', 'messy yard', 'window broken', 'read a pet', 'mistreatment of a human'
    ]
    stemmedArrests = map(getStemmedAndTokenizedArrest, newArrests)
    test_vect = vectorizer.transform(stemmedArrests)

    x_train_vect, x_test_vect, y_train_enc, y_test_enc = getSplitAndEncodedData(x, y)

    SVM = SVC(C=100.0, kernel='linear', degree=3, gamma=.1)
    SVM.fit(x_train_vect, y_train_enc)

    predictions = SVM.predict(test_vect)
    print(encoder.inverse_transform(predictions))

    score = SVM.score(x_test_vect, y_test_enc)
    print('SVM:', score)