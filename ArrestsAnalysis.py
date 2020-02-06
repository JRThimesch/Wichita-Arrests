import pandas as pd

if __name__ == "__main__":
    trueData = pd.read_csv('data/trueData.csv', sep='|')
    fakeData = pd.read_csv('data/fakeData.csv', sep='|')

    combinedData = trueData.append(fakeData)
    #print(combinedData['tags'])
    tagsCount = combinedData['tags'].value_counts().sort_index()
    arrestsCount = combinedData['arrests'].value_counts().sort_index()
    uniqueArrests = pd.Series(trueData['arrests']).unique().tolist()
    prop = trueData[(trueData['tags'] == 'Animal Cruelty')] 
    print(prop['arrests'].unique())
    #fakeDataDict = {'arrests' : fakeArrests, 
        #'tags' : fakeTags, 'stemmed' : fakeStemmedArrests}

    #print(tagsCount)
