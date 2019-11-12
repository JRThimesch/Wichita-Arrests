import pandas as pd
import numpy as np
import sys
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

stemmer = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')

def svc_param_selection(X, y, nfolds):
    Cs = [0.001, 0.01, 0.1, 1, 10, 100, 500, 1000, 10000]
    gammas = [0.001, 0.01, 0.1, 1, 10, 100]
    param_grid = {'C': Cs, 'gamma' : gammas}
    grid_search = GridSearchCV(SVC(kernel='rbf'), param_grid, cv=nfolds)
    grid_search.fit(X, y)
    grid_search.best_params_
    return grid_search.best_params_

def getPredictions(_predictions):
    numbers = np.arange((len(encoder.classes_)))
    for prediction in _predictions:
        if prediction not in numbers:
            yield 'Unknown'
        else:
            yield encoder.classes_[prediction]
    
def getStemmedAndTokenizedArrest(_arrest):
    _arrest = _arrest.lower()
    _arrest = _arrest.replace(':', '')
    _arrest = _arrest.replace('/', ' ')
    tokens = tokenizer.tokenize(_arrest)
    filteredWords = filter(lambda token: token not in stopwords.words('english'), tokens)
    stemmedArrest = [stemmer.stem(word) for word in filteredWords]
    tokenizedAndStemmedArrest = ' '.join(stemmedArrest)
    return tokenizedAndStemmedArrest

data = pd.read_csv('data/tagData.csv', delimiter='|')
np.set_printoptions(threshold=sys.maxsize)

vectorizer = TfidfVectorizer()
encoder = LabelEncoder()

x = data['stemmed']
y = data['tags']

vectorizer.fit(x)
encoder.fit(y)


newArrests = [
    'threaten', 'entering wrong way', 'entering after hours', 'possession weapons',
    'school bus sign', 'destruction of personal property: vehicle', 'grand theft auto'
]
stemmedArrests = map(getStemmedAndTokenizedArrest, newArrests)
test_vect = vectorizer.transform(stemmedArrests)


x_train, x_test, y_train, y_test = train_test_split(x, y, 
    test_size=0.3, random_state=321)

x_train_vect = vectorizer.transform(x_train)
x_test_vect = vectorizer.transform(x_test)
y_train_enc = encoder.transform(y_train)
y_test_enc = encoder.transform(y_test)
#print(x_train_vect.shape, x_test_vect.shape, y_train_enc.shape, y_test_enc.shape)

SVM = SVC(C=100.0, kernel='linear', degree=3, gamma=.1)
SVM.fit(x_train_vect, y_train_enc)

#print(svc_param_selection(x_train_vect, y_train_enc, 3))

predictions = SVM.predict(test_vect)
print(encoder.inverse_transform(predictions))

score = SVM.score(x_test_vect, y_test_enc)
print('SVM:', score)

#print(y_test_enc)
#print(predictions)

#linearRegression = LinearRegression()
#linearRegression.fit(x_train_vect, y_train_enc)

#predictions = linearRegression.predict(test_vect)
#print(encoder.inverse_transform(predictions))

#score = linearRegression.score(x_test_vect, y_test_enc)
#print('LinearRegression:', score)

#linearRegression.fit(x_train_vect, y_train_enc)
#predictions = linearRegression.predict(x_test_vect)
#print(y_test_enc.shape, predictions.shape)
#score = linearRegression.score(y_test_enc, predictions)
#print(score)

#pd.set_option('display.max_rows', 10000)
#predictions = [i for i in getPredictions(predictions)]
#actuals = encoder.inverse_transform(y_test)
#dataDict = {'arrest' : x_test, 'actual' : actuals, 'prediction' : predictions}
#df = pd.DataFrame(data=dataDict)
#print(df)
#incorrects = df.loc[df['actual'] != df['prediction']]
#print(incorrects)
#print(incorrects.shape, y_test.shape, len(predictions), df.shape)

#print(score)
