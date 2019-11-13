    def getSeparatedArrests(_dataframe):
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

    print(learningDataCounts)