import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc, roc_auc_score

np.set_printoptions(threshold=sys.maxsize)

def getSVCParameters(_x_train, _y_train):
    paramGridSVC = [
        {
            'loss' : ['squared_hinge'], 
            'C': [0.01, 0.1, 1, 10, 100],
            'tol': [1e-9, 1e-7, 1e-6, 1e-5, 1e-3],
            'max_iter': [10, 100, 1000, 10000, 20000, 25000]
        }
    ]

    gridSearch = GridSearchCV(LinearSVC(), paramGridSVC, cv=5, scoring='f1_weighted')
    gridSearch.fit(_x_train, _y_train)

    # Modified from StackOverflow
    means = gridSearch.cv_results_['mean_test_score']
    stds = gridSearch.cv_results_['std_test_score']
    for mean, params in zip(means, gridSearch.cv_results_['params']):
            print("%0.5f for %r" % (mean, params))

    return gridSearch.best_params_
    
def getStemmedAndTokenizedArrest(_arrest):
    stemmer = PorterStemmer()
    tokenizer = RegexpTokenizer(r'\w+')

    _arrest = _arrest.lower().replace(':', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ')
    _arrest = _arrest.replace(',', ' ').replace("'", '')
    
    # Remove numbers from arrest if they exist
    if not _arrest.replace(' ', '').isalpha():
        _arrest = ''.join([i for i in _arrest if not i.isdigit()])

    tokens = tokenizer.tokenize(_arrest)
    filteredWords = filter(lambda token: token not in stopwords.words('english'), tokens)
    stemmedArrest = map(stemmer.stem, filteredWords)
    tokenizedAndStemmedArrest = ' '.join(stemmedArrest)
    return tokenizedAndStemmedArrest

def plotTrainingData():
    features = y_train
    unique, counts = np.unique(features, return_counts=True)
    print(unique, counts)
    plt.figure()
    plt.title('Classes Bar Graph y')
    plt.bar(unique, height=counts, color='skyblue', ec='black')
    plt.xticks(rotation=90)
    plt.show()

def scoreModel(_model, _x, _y):
    score = _model.score(_x, _y)
    print(_model, 'Score:', score)

def identifyWeakPoints():
    indices = np.where(y_test != predictions)
    misclassified = np.take(trueData['stems'], indices[0])
    unique, counts = np.unique(misclassified, return_counts=True)
    dictCounts = dict(zip(unique, counts))
    dictCountsSorted = {k: v for k, v in sorted(dictCounts.items(), key=lambda item: item[1])}
    print(dictCountsSorted)
    misclassifiedUnique = [k for k, v in dictCountsSorted.items()]
    print(misclassifiedUnique)
    misclassifiedTags = encoder.inverse_transform(LinearSVC.predict(vectorizer.transform(misclassifiedUnique)))
    print(misclassifiedTags)

    misclassifiedIndex = np.where(misclassifiedTags == 'Procurement')
    misclassifiedLabels = np.take(misclassifiedUnique, misclassifiedIndex[0])
    print(misclassifiedLabels)

def showConfusionMatrix(_true, _predictions):
    confusionMatrix = confusion_matrix(_true, _predictions)
    plt.matshow(confusionMatrix)
    plt.colorbar()
    plt.show()

def getPredictionsTrue(_model, _test):
    predictions_enc = _model.predict(_test)
    predictions = encoder.inverse_transform(predictions_enc)
    return predictions

if __name__ == "__main__":
    vectorizer = TfidfVectorizer(ngram_range=(1,2), max_df=.11)
    encoder = LabelEncoder()

    lawData = pd.read_csv('data/lawData.csv', sep='|')
    trueData = pd.read_csv('data/trueData.csv', sep='|')

    x_train = lawData['stems']
    y_train = lawData['tags']
    x_test = trueData['stems']
    y_test = trueData['tags']

    x_train_vect = vectorizer.fit_transform(x_train)
    y_train_enc = encoder.fit_transform(y_train)
    x_test_vect = vectorizer.transform(x_test)
    y_test_enc = encoder.transform(y_test)

    #plotTrainingData()

    linearSVC = LinearSVC(C = 10, tol=1e-3, max_iter=1000)
    linearSVC.fit(x_train_vect, y_train_enc)

    #scoreModel(linearSVC, x_test_vect, y_test_enc)
    
    predictions = getPredictionsTrue(linearSVC, x_test_vect)

    report = classification_report(y_test, predictions, target_names=encoder.classes_)
    print(report)

    #showConfusionMatrix(y_test, predictions)

    print(getSVCParameters(x_train_vect, y_train_enc))