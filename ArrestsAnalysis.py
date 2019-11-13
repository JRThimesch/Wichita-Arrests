"""     def getSeparatedArrests(_dataframe):
    listOfArrests = _dataframe['Arrests'].tolist()
    for arrests in listOfArrests:
        for arrest in arrests:
            yield arrest

    
    arrests = [arrest for arrest in arrestsSeries.tolist() if arrest != 'No arrests listed.']
    tags = getTagsFromArrests(arrests)
    #stemmedArrests = [getStemmedAndTokenizedArrest(arrest) for arrest in arrests]
    #dataDict = {'arrests' : arrests, 'tags' : tags, 'stemmed' : stemmedArrests}
    uniqueArrests = pd.Series(arrestsSeries.unique()).tolist()
    uniqueStems = map(getStemmedAndTokenizedArrest, uniqueArrests)
    uniqueTags = getTagsFromArrests(uniqueArrests)
    uniques = pd.DataFrame(data=[uniqueArrests, uniqueTags, uniqueStems], columns=['arrest', 'tag', 'stem'])
    print(uniques)
    #learningData = pd.DataFrame(data=dataDict)
    #learningData.to_csv('data/tagData.csv', sep = '|')
    learningDataCounts = pd.DataFrame(data=pd.Series(tags).value_counts().sort_index())

    print(learningDataCounts) """

import os
import pandas as pd

def getCSVs(_path):
    files = os.listdir(_path)
    return [_path + file for file in files if file.endswith('.csv')]

def getFullDataFrame(_CSVs):
    fullDataframe = pd.DataFrame(data=[])
    for csv in _CSVs:
        print('Opening...', csv)
        dfCSV = pd.read_csv(csv, sep='|', index_col=0, converters=conversionDict)
        fullDataframe = fullDataframe.append(dfCSV, ignore_index=True)
    return fullDataframe

if __name__ == "__main__":
    conversionDict = {"Arrests": lambda x: x.strip("[]").split("', ")}
    CSVs = getCSVs('CSVs/')
    
    dfFull = getFullDataFrame(CSVs)
    
    arrestsFull = dfFull['Arrests'] 
    #print(arrestsFull)
    for listOfArrests in arrestsFull:
        for arrest in listOfArrests:
            print(arrest.strip("'\""))