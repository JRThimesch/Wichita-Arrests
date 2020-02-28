from flask import Flask, url_for, render_template, jsonify, request
from operator import itemgetter
from datetime import datetime, timedelta, date
import json, random, itertools, os
import sqlalchemy as SQL
from sqlalchemy import create_engine, func, and_, or_, desc, literal_column
from sqlalchemy.types import Integer, Date, Float
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import cast, case, literal, extract
from contextlib import contextmanager
from Models import ArrestInfo, ArrestRecord

user = os.getenv('Postgres_USER')
password = os.getenv('Postgres_PASSWORD')

dbURL = f'postgresql+psycopg2://{user}:{password}@localhost:5432/wichitaArrests'
dbURL2 = f'postgresql+psycopg2://{user}:{password}@localhost:5432/wichita-arrests'
engine = create_engine(dbURL)
engine2 = create_engine(dbURL2)
Session = sessionmaker(bind=engine)
conn = engine2.connect()
metadata = SQL.MetaData()
wichitaArrests = SQL.Table('wichita-arrests', metadata, autoload=True, autoload_with=engine2)

app = Flask(__name__, template_folder = "templates")

DEV_MODE = True
MAX_ARRESTS = 2500
splitList = lambda x: x.split(';')

@contextmanager
def sessionManager():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def loadJSON(_file):
    with open(_file) as f:
        _dict = json.load(f)
    return _dict

def getListQuery(_query):
    return list(list(zip(*_query))[0])

def getSingleQuery(_query):
    return list(zip(*_query))[0]

def getGroupingData(_s, _queryColumn, _groupingColumn, _labels, _joinTable=ArrestRecord, _queryType = 'distinct'):
    # QUERY METHOD NEEDS TO BE DIFFERENT FOR TIME
    # TIMES ARE EXACT AND WOULD MAKE ANALYSIS AWFUL IF DONE UNIQUELY
    if _queryColumn == ArrestRecord.time:
        dataSubq = _s.query(func.substr(_queryColumn, 0, 4).label('time'))\
            .distinct(func.substr(_queryColumn, 0, 4))\
            .filter(_queryColumn != None)\
            .subquery()
        #print(_s.query(dataSubq).all())
    elif _queryColumn != ArrestRecord.time:
        dataSubq = _s.query(_queryColumn)\
            .distinct(_queryColumn)\
            .filter(and_(_queryColumn != None, _queryColumn.in_(_labels)))\
            .subquery()

    categorySubq = _s.query(_groupingColumn)\
        .distinct(_groupingColumn)\
        .subquery()

    cartesionProduct = _s.query(dataSubq, categorySubq)\
        .join(categorySubq, literal(True))\
        .subquery()

    if _queryType == 'distinct':
        if _queryColumn == ArrestRecord.time:
            distinctCountSubq = _s.query(func.substr(_queryColumn, 0, 4).label('time'), _groupingColumn)\
                .join(_joinTable)\
                .distinct(ArrestRecord.recordID, func.substr(_queryColumn, 0, 4))\
                .filter(_queryColumn != None)\
                .group_by(ArrestRecord.recordID, func.substr(_queryColumn, 0, 4))\
                .subquery()

        elif _queryColumn != ArrestRecord.time:
            distinctCountSubq = _s.query(_queryColumn, _groupingColumn)\
                .join(_joinTable)\
                .distinct(ArrestRecord.recordID, _queryColumn)\
                .filter(_queryColumn != None)\
                .group_by(ArrestRecord.recordID, _queryColumn)\
                .subquery()
        
        # IF/ELSE BLOCK FOR SELECTING DISTINCT COUNTS FOR CATEGORY COLUMN
        if _queryColumn == ArrestInfo.arrest:
            distinctCountColumn = distinctCountSubq.c.arrest
        elif _queryColumn == ArrestInfo.tag:
            distinctCountColumn = distinctCountSubq.c.tag
        elif _queryColumn == ArrestInfo.group:
            distinctCountColumn = distinctCountSubq.c.group
        elif _queryColumn == ArrestRecord.age:
            distinctCountColumn = distinctCountSubq.c.age
        elif _queryColumn == ArrestRecord.timeOfYear:
            distinctCountColumn = distinctCountSubq.c.timeOfYear
        elif _queryColumn == ArrestRecord.dayOfTheWeek:
            distinctCountColumn = distinctCountSubq.c.dayOfTheWeek
        elif _queryColumn == ArrestRecord.date:
            distinctCountColumn = distinctCountSubq.c.date
        elif _queryColumn == ArrestRecord.time:
            distinctCountColumn = distinctCountSubq.c.time
        elif _queryColumn == ArrestRecord.sex:
            distinctCountColumn = distinctCountSubq.c.sex

        # IF/ELSE BLOCK FOR SELECTING GROUPING COLUMNS
        if _groupingColumn == ArrestRecord.dayOfTheWeek:
            distinctCategoryCountColumn = distinctCountSubq.c.dayOfTheWeek
        elif _groupingColumn == ArrestRecord.sex:
            distinctCategoryCountColumn = distinctCountSubq.c.sex
        elif _groupingColumn == ArrestRecord.timeOfDay:
            distinctCategoryCountColumn = distinctCountSubq.c.timeOfDay
        elif _groupingColumn == ArrestRecord.age:
            distinctCategoryCountColumn = distinctCountSubq.c.age
            query = _s.query(cast(func.avg(distinctCategoryCountColumn), Float).label('count'),
                distinctCountColumn, literal(0).label('avg'))\
                .group_by(distinctCountColumn)\
                .order_by(distinctCountColumn)\
                .all()
            return query

        if _queryColumn == ArrestRecord.time:
            countSubq = _s.query(distinctCountColumn, distinctCategoryCountColumn, 
                func.count(distinctCategoryCountColumn).label('count'))\
                .group_by(distinctCountColumn, distinctCategoryCountColumn)\
                .subquery()
            
        elif _queryColumn != ArrestRecord.time:
            countSubq = _s.query(distinctCountColumn, distinctCategoryCountColumn, 
                func.count(distinctCategoryCountColumn).label('count'))\
                .group_by(distinctCountColumn, distinctCategoryCountColumn)\
                .subquery()
        #print(_s.query(countSubq).all())

    elif _queryType == 'charges':
        if _queryColumn == ArrestRecord.time:
            timeSplitSubq = _s.query(func.substr(_queryColumn, 0, 4).label('time'), _groupingColumn)\
                .join(ArrestInfo)\
                .filter(_queryColumn != None)\
                .subquery()

            if _groupingColumn == ArrestRecord.dayOfTheWeek:
                timeCategoryCountColumn = timeSplitSubq.c.dayOfTheWeek
            elif _groupingColumn == ArrestRecord.sex:
                timeCategoryCountColumn = timeSplitSubq.c.sex
            elif _groupingColumn == ArrestRecord.timeOfDay:
                timeCategoryCountColumn = timeSplitSubq.c.timeOfDay
            elif _groupingColumn == ArrestRecord.age:
                timeCategoryCountColumn = timeSplitSubq.c.age
                query = _s.query(cast(func.avg(timeCategoryCountColumn), Float).label('count'),
                    timeSplitSubq.c.time, literal(0).label('avg'))\
                    .group_by(timeSplitSubq.c.time)\
                    .all()
                return query

            countSubq = _s.query(timeSplitSubq.c.time, timeCategoryCountColumn, 
                    func.count(timeCategoryCountColumn).label('count'))\
                .group_by(timeSplitSubq.c.time, timeCategoryCountColumn)\
                .subquery()
        elif _queryColumn != ArrestRecord.time:
            if _groupingColumn == ArrestRecord.age:
                query = _s.query(cast(func.avg(_groupingColumn), Float).label('count'), 
                    _queryColumn, literal(0).label('avg'))\
                    .group_by(_queryColumn)\
                    .order_by(_queryColumn)\
                    .all()
                return query
            countSubq = _s.query(_queryColumn, _groupingColumn, 
                    func.count(_groupingColumn).label('count'))\
                .join(_joinTable)\
                .filter(_queryColumn != None)\
                .group_by(_queryColumn, _groupingColumn)\
                .subquery()
            

    # IF/ELSE BLOCK FOR DECLARING CATEGORY COLUMNS
    if _queryColumn == ArrestInfo.arrest:
        countColumn = countSubq.c.arrest
        productColumn = cartesionProduct.c.arrest
        sortCase = productColumn
    elif _queryColumn == ArrestInfo.tag:
        countColumn = countSubq.c.tag
        productColumn = cartesionProduct.c.tag
        sortCase = productColumn
    elif _queryColumn == ArrestInfo.group:
        countColumn = countSubq.c.group
        productColumn = cartesionProduct.c.group
        sortCase = productColumn
    elif _queryColumn == ArrestRecord.age:
        countColumn = countSubq.c.age
        productColumn = cartesionProduct.c.age
        sortCase = productColumn
    elif _queryColumn == ArrestRecord.timeOfYear:
        countColumn = countSubq.c.timeOfYear
        productColumn = cartesionProduct.c.timeOfYear
        sortCase = productColumn
    elif _queryColumn == ArrestRecord.dayOfTheWeek:
        countColumn = countSubq.c.dayOfTheWeek
        productColumn = cartesionProduct.c.dayOfTheWeek
        sortCase = case([
            (cartesionProduct.c.dayOfTheWeek == "Sunday", 1),
            (cartesionProduct.c.dayOfTheWeek == "Monday", 2),
            (cartesionProduct.c.dayOfTheWeek == "Tuesday", 3),
            (cartesionProduct.c.dayOfTheWeek == "Wednesday", 4),
            (cartesionProduct.c.dayOfTheWeek == "Thursday", 5),
            (cartesionProduct.c.dayOfTheWeek == "Friday", 6),
            (cartesionProduct.c.dayOfTheWeek == "Saturday", 7)
        ])
    elif _queryColumn == ArrestRecord.date:
        countColumn = countSubq.c.date
        productColumn = cartesionProduct.c.date
        sortCase = productColumn
    elif _queryColumn == ArrestRecord.time:
        countColumn = countSubq.c.time
        productColumn = cartesionProduct.c.time
        sortCase = productColumn
    elif _queryColumn == ArrestRecord.sex:
        countColumn = countSubq.c.sex
        productColumn = cartesionProduct.c.sex
        sortCase = productColumn

    # IF/ELSE BLOCK FOR DECLARING GROUPING COLUMNS
    if _groupingColumn == ArrestRecord.dayOfTheWeek:
        countCategoryColumn = countSubq.c.dayOfTheWeek
        productCategoryColumn = cartesionProduct.c.dayOfTheWeek
        allowedGroupings = ["Sunday", "Monday", "Tuesday", 
            "Wednesday", "Thursday", "Friday", "Saturday"]
        orderCase = case([
            (productCategoryColumn == "Sunday", 1),
            (productCategoryColumn == "Monday", 2),
            (productCategoryColumn == "Tuesday", 3),
            (productCategoryColumn == "Wednesday", 4),
            (productCategoryColumn == "Thursday", 5),
            (productCategoryColumn == "Friday", 6),
            (productCategoryColumn == "Saturday", 7)
        ])
    elif _groupingColumn == ArrestRecord.sex:
        countCategoryColumn = countSubq.c.sex
        productCategoryColumn = cartesionProduct.c.sex
        allowedGroupings = ["MALE", "FEMALE"]
        orderCase = case([
            (productCategoryColumn == "MALE", 1),
            (productCategoryColumn == "FEMALE", 2)
        ])
    elif _groupingColumn == ArrestRecord.timeOfDay:
        countCategoryColumn = countSubq.c.timeOfDay
        productCategoryColumn = cartesionProduct.c.timeOfDay
        allowedGroupings = ["DAY", "NIGHT"]
        orderCase = case([
            (productCategoryColumn == "DAY", 1),
            (productCategoryColumn == "NIGHT", 2)
        ])

    caseCountStatement = case([(countSubq.c.count > 0, countSubq.c.count)], else_=0)
    
    query = _s.query(caseCountStatement, cartesionProduct)\
        .outerjoin(countSubq, and_(countCategoryColumn == productCategoryColumn,
            countColumn == productColumn))\
        .filter(productCategoryColumn.in_(allowedGroupings))\
        .order_by(sortCase, orderCase)\
        .all()

    # Not sorted correctly by ORDER BY statements, easier to do it in python
    if _queryColumn == ArrestRecord.timeOfYear:
        query = sorted(query, key=lambda x: datetime.strptime(x[1], '%B %Y'))

    return query

def splitListInChunks(_list, _n):
    return [_list[i * _n:(i + 1) * _n] for i in range((len(_list) + _n - 1) // _n)]

def getNumbersFromQuery(_q):
    queryAsList = list(map(list, zip(*_q)))
    subListLength = len(set(queryAsList[2]))
    return splitListInChunks(queryAsList[0], subListLength)

def getRespectiveQueryColumn(_string):
    if _string == "groups":
        return ArrestInfo.group
    elif _string == "tags":
        return ArrestInfo.tag
    elif _string == "arrests":
        return ArrestInfo.arrest
    elif _string == "ages":
        return ArrestRecord.age
    elif _string == "dates":
        return ArrestRecord.date
    elif _string == "genders":
        return ArrestRecord.sex
    elif _string == "times":
        return ArrestRecord.time
    elif _string == "days":
        return ArrestRecord.dayOfTheWeek
    elif _string == "months":
        return ArrestRecord.timeOfYear

def getRespectiveGroupingColumn(_string):
    if _string == "days":
        return ArrestRecord.dayOfTheWeek
    elif _string == "times":
        return ArrestRecord.timeOfDay
    elif _string == "genders":
        return ArrestRecord.sex
    elif _string == "ages":
        return ArrestRecord.age
    
def getRespectiveSubqueryColumn(_string, _table):
    if _string == "groups":
        return _table.c.group
    elif _string == "tags":
        return _table.c.tag
    elif _string == "arrests":
        return _table.c.arrest
    elif _string == "ages":
        return _table.c.age
    elif _string == "dates":
        return _table.c.date
    elif _string == "genders":
        return _table.c.sex
    elif _string == "times":
        return _table.c.time
    elif _string == "days":
        return _table.c.dayOfTheWeek
    elif _string == "months":
        return _table.c.timeOfYear

def getCountsForGroupingData(_data):
    active = _data['dataActive']
    queryType = _data['queryType']
    grouping = _data['groupingType']
    labels = _data['labels']
    
    queriedColumn = getRespectiveQueryColumn(active)
    groupingColumn = getRespectiveGroupingColumn(grouping)

    with sessionManager() as s:
        if queryType == 'distinct':
            query = getGroupingData(s, queriedColumn, groupingColumn, labels, _joinTable=ArrestInfo)
        elif queryType == 'charges':
            query = getGroupingData(s, queriedColumn, groupingColumn, labels, _joinTable=ArrestInfo, _queryType = 'charges')
        counts = getNumbersFromQuery(query)
    return counts

def getArrests():
    colorsDict = loadJSON("./static/js/Filters.json")   
    with sessionManager() as s:
        # QUERY TYPE DOES NOT MATTER HERE, ARRESTS ARE UNIQUE AND NO DUPLICATES APPEAR IN A RECORD
        # YOU CANNOT BE CHARGED FOR THE SAME ARREST TWICE
        query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
            .filter(and_(ArrestInfo.arrest != "No arrests listed.", ArrestInfo.arrest != None)) \
            .group_by(ArrestInfo.group, ArrestInfo.arrest) \
            .all()

    arrests = [i[0] for i in query]
    counts = [i[1] for i in query]
    groups = [i[2] for i in query]

    sortedZip = sorted(zip(arrests, counts, groups))
    arrests, counts, groups = zip(*sortedZip)

    colors = [next(i['color'] for i in colorsDict if i['identifier'] == group) for group in groups]

    print([[i['tag'] for i in colorsDict if i['identifier'] == group] for group in list(set([i['identifier'] for i in colorsDict]))])

    return arrests, counts, colors

def getTags(_queryType):
    colorsDict = loadJSON("./static/js/Filters.json")

    with sessionManager() as s:
        if _queryType == 'charges':
            query = s.query(ArrestInfo.tag, func.count(ArrestInfo.tag))\
                .filter(ArrestInfo.tag != None)\
                .group_by(ArrestInfo.tag) \
                .all()
        elif _queryType == 'distinct':
            subquery = s.query(ArrestRecord.recordID, ArrestInfo.tag)\
                .join(ArrestInfo)\
                .filter(ArrestInfo.tag != None)\
                .distinct(ArrestRecord.recordID, ArrestInfo.tag)\
                .subquery()
            query = s.query(subquery.c.tag, func.count(subquery.c.tag))\
                .group_by(subquery.c.tag)\
                .all()

    tags = [i[0] for i in query]
    counts = [i[1] for i in query]

    sortedZip = sorted(zip(tags, counts))
    tags, counts = zip(*sortedZip)

    colors = [next(i['color'] for i in colorsDict if i['tag'] == tag) for tag in tags]

    return tags, counts, colors

def isGroupColorQuery(_queryColumn):
    return _queryColumn == ArrestInfo.arrest or _queryColumn == ArrestInfo.tag or _queryColumn == ArrestInfo.group

def getRespectiveSortingCase(_string, _column):
    if _string == "groups":
        return _column
    elif _string == "tags":
        return _column
    elif _string == "arrests":
        return _column
    elif _string == "ages":
        return _column
    elif _string == "dates":
        return _column
    elif _string == "genders":
        return case([
            (_column == "MALE", 1),
            (_column == "FEMALE", 2),
        ])
    elif _string == "times":
        return _column
    elif _string == "days":
        return case([
            (_column == "Sunday", 1),
            (_column == "Monday", 2),
            (_column == "Tuesday", 3),
            (_column == "Wednesday", 4),
            (_column == "Thursday", 5),
            (_column == "Friday", 6),
            (_column == "Saturday", 7)
        ])
    elif _string == "months":
        return _column

def getRespectiveFilter(_string, _column):
    if _string == "groups":
        return (_column != None)
    elif _string == "tags":
        return (_column != None)
    elif _string == "arrests":
        return and_(_column != None, _column != 'No arrests listed.')
    elif _string == "ages":
        return (_column != None)
    elif _string == "dates":
        return (_column != None)
    elif _string == "genders":
        return (_column != None)
    elif _string == "times":
        return (_column != None)
    elif _string == "days":
        return (_column != None)
    elif _string == "months":
        return (_column != None)

def getRespectiveColors(_string, _labels, _supportList = None):
    colorsDict = loadJSON("./static/js/FiltersImproved.json")
    monthDict = {
        "January": "#0095FF",
        "February": "#10A4CC",
        "March": "#20B39A",
        "April": "#30C268",
        "May": "#40D136",
        "June": "#6FC628",
        "July": "#9FBB1B",
        "August": "#CFB00D",
        "September": "#FFA600",
        "October": "#B19B45",
        "November": "#64918B",
        "December": "#1787D1"
    }
    dateDict = {
        "01": "#0095FF",
        "02": "#10A4CC",
        "03": "#20B39A",
        "04": "#30C268",
        "05": "#40D136",
        "06": "#6FC628",
        "07": "#9FBB1B",
        "08": "#CFB00D",
        "09": "#FFA600",
        "10": "#B19B45",
        "11": "#64918B",
        "12": "#1787D1"
    }

    if _string == "groups":
        return [next(i['color'] for i in colorsDict if i['group'] == group) for group in _supportList]
    elif _string == "tags":
        return [next(i['color'] for i in colorsDict if i['group'] == group) for group in _supportList]
    elif _string == "arrests":
        return [next(i['color'] for i in colorsDict if i['group'] == group) for group in _supportList]
    elif _string == "ages":
        return ['#def123'] * len(_labels)
    elif _string == "dates":
        return [dateDict[i.partition('/')[0]] for i in _labels]
    elif _string == "genders":
        return ['#80d8f2', '#eb88d4']
    elif _string == "times":
        return ["#00044A", "#051553", "#0A275C", "#0F3866", 
            "#144A6F", "#195B78", "#1E6D82", "#237E8B", 
            "#289094", "#2DA19E", "#32B3A7", "#37C4B0", 
            "#3CD6BA", "#36C2AF", "#31AFA5", "#2B9C9B", 
            "#268991", "#207687", "#1B637C", "#155072", 
            "#103D68", "#0A2A5E", "#051754", "#00044A"]
    elif _string == "days":
        return ["#FF5500", "#FF6D00", "#FF8500", 
            "#FF9D00", "#FFBC22", "#FFDB44", "#FFFA66"]
    elif _string == "months":
        return [monthDict[i.partition(' ')[0]] for i in _labels]

def getQueryData(_data):
    print(_data)
    queryString = _data['dataActive']
    queryString = 'dates'
    queryColumn = getRespectiveQueryColumn(queryString)
    queryType = _data['queryType']
    queryType = 'charges'

    if isGroupColorQuery(queryColumn):
        joinTable = ArrestRecord
    else:
        joinTable = ArrestInfo

    filterQuery = getRespectiveFilter(queryString, queryColumn)
    sortingCase = getRespectiveSortingCase(queryString, queryColumn)

    with sessionManager() as s:
        if queryType == 'charges':
            if isGroupColorQuery(queryColumn):
                query = s.query(queryColumn, func.count(queryColumn).label('count'),
                        ArrestInfo.group)\
                    .join(joinTable)\
                    .filter(filterQuery)\
                    .order_by(sortingCase)\
                    .group_by(queryColumn, ArrestInfo.group)\
                    .all()
            else:
                query = s.query(queryColumn, func.count(queryColumn).label('count'))\
                    .join(joinTable)\
                    .filter(filterQuery)\
                    .order_by(sortingCase)\
                    .group_by(queryColumn)\
                    .all()
        elif queryType == 'distinct':
            distinctQuerySubq = s.query(queryColumn, ArrestInfo.group)\
                .join(joinTable)\
                .distinct(ArrestRecord.recordID, queryColumn)\
                .filter(filterQuery)\
                .group_by(ArrestRecord.recordID, queryColumn, ArrestInfo.group)\
                .subquery()

            subqColumn = getRespectiveSubqueryColumn(queryString, distinctQuerySubq)
            sortingCase = getRespectiveSortingCase(queryString, subqColumn)

            if isGroupColorQuery(queryColumn):
                # Tags/Arrests/Groups need an extra query on the group column
                # Facilitates color selection
                query = s.query(subqColumn, func.count(subqColumn).label('count'), 
                        distinctQuerySubq.c.group)\
                    .group_by(subqColumn, distinctQuerySubq.c.group)\
                    .order_by(subqColumn)\
                    .all()
            else:
                query = s.query(subqColumn, func.count(subqColumn).label('count'))\
                    .group_by(subqColumn)\
                    .order_by(sortingCase)\
                    .all()

    try:
        labels, counts = zip(*query)
        if queryString == 'dates':
            labels = [date.strftime(i[0], "%m/%d/%Y") for i in query]
        colors = getRespectiveColors(queryString, labels)
    except ValueError:
        labels, counts, supportGroups = zip(*query)
        colors = getRespectiveColors(queryString, labels, _supportList=supportGroups)
        
    return labels, counts, colors

def getGroups(_queryType):
    colorsDict = loadJSON("./static/js/Filters.json")

    with sessionManager() as s:
        groups = getSingleQuery(s.query(ArrestInfo.group)\
        .filter(ArrestInfo.group != None)\
        .group_by(ArrestInfo.group)\
        .distinct())
        if _queryType == 'charges':
            counts = [s.query(ArrestInfo.group)
                .filter(ArrestInfo.group == group)
                .count() for group in groups]
        elif _queryType == 'distinct':
            # dont need to join? just use the foreign key instead of recordid
            counts =  [s.query(ArrestRecord.recordID, ArrestInfo.group)\
                .join(ArrestInfo)\
                .distinct(ArrestRecord.recordID, ArrestInfo.group)\
                .filter(ArrestInfo.group == group)\
                .count() for group in groups]

    colors = [next(i['color'] for i in colorsDict if i['identifier'] == group) for group in groups]
    return groups, counts, colors

def getDatesData(_queryType):
    with sessionManager() as s:
        if _queryType == 'charges':
            query = s.query(ArrestRecord.date, func.count(ArrestRecord.date))\
                .join(ArrestInfo)\
                .group_by(ArrestRecord.date) \
                .all()
        elif _queryType == 'distinct':
            query = s.query(ArrestRecord.date, func.count(ArrestRecord.date))\
                .group_by(ArrestRecord.date) \
                .all()

    initialSortedQuery = sorted(query)
    queriedDates = [i[0] for i in initialSortedQuery]
    
    startDate = initialSortedQuery[0][0]
    endDate = initialSortedQuery[-1][0]

    generatedDates = [startDate + timedelta(days=i) 
        for i in range(0, (endDate - startDate + timedelta(days=1)).days)]

    missingDates = list(set(generatedDates).difference(queriedDates))
    missingTuples = [(date, 0) for date in missingDates]

    initialSortedQuery.extend(missingTuples)
    finalSortedQuery = sorted(initialSortedQuery)

    dates = [date.strftime(i[0], "%m/%d/%Y") for i in finalSortedQuery]

    counts = [i[1] for i in finalSortedQuery]


    colorDict = {
        "01": "#0095FF",
        "02": "#10A4CC",
        "03": "#20B39A",
        "04": "#30C268",
        "05": "#40D136",
        "06": "#6FC628",
        "07": "#9FBB1B",
        "08": "#CFB00D",
        "09": "#FFA600",
        "10": "#B19B45",
        "11": "#64918B",
        "12": "#1787D1"
    }

    colors = [colorDict[date.partition('/')[0]] for date in dates]

    return dates, counts, colors

def getTimes(_queryType):
    hours = [str(x) + ':' if x >= 10 else '0' + str(x) + ':' for x in range(0, 24)]

    with sessionManager() as s:
        if _queryType == 'charges':
            counts = [s.query(ArrestRecord.time)\
                .join(ArrestInfo)\
                .filter(ArrestRecord.time.contains(hour))\
                .count() for hour in hours]
        elif _queryType == 'distinct':
            counts = [s.query(ArrestRecord.time)\
                .filter(ArrestRecord.time.contains(hour))\
                .count() for hour in hours]

    times = [hour + '00 - ' + hour + '59' for hour in hours]

    colors = ["#00044A", "#051553", "#0A275C", "#0F3866", 
    "#144A6F", "#195B78", "#1E6D82", "#237E8B", 
    "#289094", "#2DA19E", "#32B3A7", "#37C4B0", 
    "#3CD6BA", "#36C2AF", "#31AFA5", "#2B9C9B", 
    "#268991", "#207687", "#1B637C", "#155072", 
    "#103D68", "#0A2A5E", "#051754", "#00044A"]

    return times, counts, colors

def getDays(_queryType):
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
        'Thursday', 'Friday', 'Saturday']

    with sessionManager() as s:
        if _queryType == 'charges':
            query = s.query(ArrestRecord.dayOfTheWeek, func.count(ArrestRecord.dayOfTheWeek))\
                .group_by(ArrestRecord.dayOfTheWeek) \
                .all()
        elif _queryType == 'distinct':
            subquery = s.query(ArrestRecord.recordID, ArrestRecord.dayOfTheWeek)\
                .join(ArrestInfo)\
                .distinct(ArrestRecord.recordID, ArrestRecord.dayOfTheWeek)\
                .subquery()
            query = s.query(subquery.c.dayOfTheWeek, func.count(subquery.c.dayOfTheWeek))\
                .group_by(subquery.c.dayOfTheWeek)\
                .all()

    queryDict = dict(query)
    counts = [queryDict[day] for day in days]
    
    colors = ["#FF5500", "#FF6D00", "#FF8500", "#FF9D00", "#FFBC22", "#FFDB44", "#FFFA66"]

    return days, counts, colors

def getMonths(_queryType):
    with sessionManager() as s:
        if _queryType == 'charges':
            query = s.query(ArrestRecord.timeOfYear, func.count(ArrestRecord.timeOfYear))\
                .group_by(ArrestRecord.timeOfYear) \
                .all()
        elif _queryType == 'distinct':
            subquery = s.query(ArrestRecord.recordID, ArrestRecord.timeOfYear)\
                .join(ArrestInfo)\
                .distinct(ArrestRecord.recordID, ArrestRecord.timeOfYear)\
                .subquery()
            query = s.query(subquery.c.timeOfYear, func.count(subquery.c.timeOfYear))\
                .group_by(subquery.c.timeOfYear)\
                .all()
    months = [i[0] for i in query]
    counts = [i[1] for i in query]

    sortedZip = sorted(zip(months, counts), key=lambda x: datetime.strptime(x[0], '%B %Y'))
    months, counts = zip(*sortedZip)

    colorDict = {
        "January": "#0095FF",
        "February": "#10A4CC",
        "March": "#20B39A",
        "April": "#30C268",
        "May": "#40D136",
        "June": "#6FC628",
        "July": "#9FBB1B",
        "August": "#CFB00D",
        "September": "#FFA600",
        "October": "#B19B45",
        "November": "#64918B",
        "December": "#1787D1"
    }

    colors = [colorDict[month.partition(' ')[0]] for month in months]

    return months, counts, colors

def getAges(_queryType):
    with sessionManager() as s:
        if _queryType == 'charges':
            query = s.query(ArrestRecord.age, func.count(ArrestRecord.age))\
                .join(ArrestInfo)\
                .group_by(ArrestRecord.age) \
                .filter(ArrestRecord.age != None) \
                .all()
        elif _queryType == 'distinct':
            query = s.query(ArrestRecord.age, func.count(ArrestRecord.age))\
                .group_by(ArrestRecord.age) \
                .filter(ArrestRecord.age != None) \
                .all()

    ages = [i[0] for i in query]
    counts = [i[1] for i in query]

    sortedZip = sorted(zip(ages, counts))
    ages, counts = zip(*sortedZip)

    return ages, counts, ['#333333'] * len(counts)

def getGenders(_queryType):
    with sessionManager() as s:
        if _queryType == 'charges':
            query = s.query(ArrestRecord.sex, func.count(ArrestRecord.sex))\
                .join(ArrestInfo) \
                .group_by(ArrestRecord.sex) \
                .all()
        elif _queryType == 'distinct':
            query = s.query(ArrestRecord.sex, func.count(ArrestRecord.sex))\
                .group_by(ArrestRecord.sex) \
                .all()

    genders = [i[0] for i in query]
    counts = [i[1] for i in query]

    return genders, counts, ['#80d8f2', '#eb88d4']

def getAverageAge(s, _column, _label, _activeDays, _activeGenders, _activeTimes, _joinTable = ArrestInfo, _charges = False):
    if _charges:
        if _column == ArrestRecord.time:
            averageAgeSubq = s.query(ArrestRecord.age)\
                .join(_joinTable)\
                .group_by(ArrestInfo.arrestRecordFKey, ArrestRecord.age)\
                .filter(and_(_column.contains(_label),
                ArrestRecord.age != None,
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()
        else:
            averageAgeSubq = s.query(ArrestRecord.age)\
                .join(_joinTable)\
                .group_by(ArrestInfo.arrestRecordFKey, ArrestRecord.age)\
                .filter(and_(_column == _label,
                ArrestRecord.age != None,
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()
    else:
        if _column == ArrestRecord.time:
            averageAgeSubq = s.query(ArrestRecord.age)\
                .join(_joinTable)\
                .distinct(ArrestInfo.arrestRecordFKey)\
                .group_by(ArrestInfo.arrestRecordFKey, ArrestRecord.age)\
                .filter(and_(_column.contains(_label),
                ArrestRecord.age != None,
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()
        else:
            averageAgeSubq = s.query(ArrestRecord.age)\
                .join(_joinTable)\
                .distinct(ArrestInfo.arrestRecordFKey)\
                .group_by(ArrestInfo.arrestRecordFKey, ArrestRecord.age)\
                .filter(and_(_column == _label,
                ArrestRecord.age != None,
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()

    return s.query(cast(func.avg(averageAgeSubq.c.age), Integer)).all()[0][0]

def getGenderSubQuery(s, _column, _label, _activeDays, _activeGenders, _activeTimes, _charges = False):
    if _charges:
        if _column == ArrestRecord.time:
            return s.query(_column, ArrestRecord.sex)\
                .join(ArrestInfo)\
                .filter(and_(_column.contains(_label),
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()
        else:
            return s.query(_column, ArrestRecord.sex)\
                .join(ArrestInfo)\
                .filter(and_(_column == _label,
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()
    else:
        if _column == ArrestRecord.time:
            return s.query(_column, ArrestRecord.sex)\
                .join(ArrestInfo)\
                .distinct(ArrestInfo.arrestRecordFKey)\
                .filter(and_(_column.contains(_label),
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()
        else:
            return s.query(_column, ArrestRecord.sex)\
                .join(ArrestInfo)\
                .distinct(ArrestInfo.arrestRecordFKey)\
                .filter(and_(_column == _label,
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()

def getDaysSubQuery(s, _column, _label, _activeDays, _activeGenders, _activeTimes, _charges = False):
    if _charges:
        if _column == ArrestRecord.time:
            return s.query(_column, ArrestRecord.dayOfTheWeek)\
                .join(ArrestInfo)\
                .filter(and_(_column.contains(_label),
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()
        else:
            return s.query(_column, ArrestRecord.dayOfTheWeek)\
                .join(ArrestInfo)\
                .filter(and_(_column == _label,
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()
    else:
        if _column == ArrestRecord.time:
            return s.query(_column, ArrestRecord.dayOfTheWeek)\
                .join(ArrestInfo)\
                .distinct(ArrestInfo.arrestRecordFKey)\
                .filter(and_(_column.contains(_label),
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()
        else:
            return s.query(_column, ArrestRecord.dayOfTheWeek)\
                .join(ArrestInfo)\
                .distinct(ArrestInfo.arrestRecordFKey)\
                .filter(and_(_column == _label,
                ArrestRecord.sex.in_(_activeGenders),
                ArrestRecord.timeOfDay.in_(_activeTimes),
                ArrestRecord.dayOfTheWeek.in_(_activeDays)))\
                .subquery()

def getHoverData(_data):
    activeBars = _data['activeData']['barsActive']
    label = _data['label']
    sublabel = _data['sublabel']
    activeGrouping = _data['activeData']['groupingActive']
    queryType = _data['activeData']['queryType']
    activeGenders = ('MALE', 'FEMALE')
    activeTimes = ('DAY', 'NIGHT')
    activeDays = ('Sunday', 'Monday', 'Tuesday', 'Wednesday',
        'Thursday', 'Friday', 'Saturday')
    if activeGrouping == 'genders':
        activeGenders = (sublabel, )
    elif activeGrouping == 'times':
        activeTimes = (sublabel, )
    elif activeGrouping == 'days':
        activeDays = (sublabel, )
    group = None
    tag = None
    averageAge = None
    actives = None
    colors = None
    print(_data)
    print(activeGenders, activeTimes, activeDays)
    colorDict = {
        'genders': {
            'MALE': '#80d8f2', 
            'FEMALE': '#eb88d4'
        },
        'days': {
            'Sunday': '#FF5500',
            'Monday': '#FF6D00',
            'Tuesday': '#FF8500',
            'Wednesday': '#FF9D00',
            'Thursday': '#FFBC22',
            'Friday': '#FFDB44',
            'Saturday': '#FFFA66'
        }
    }
    filtersDict = loadJSON("./static/js/FiltersImproved.json")

    with sessionManager() as s:
        if queryType == 'distinct':
            if activeBars == 'groups':
                # subq exists to get the joined table in distinct IDs
                subq = s.query(ArrestInfo.group, ArrestInfo.tag)\
                    .join(ArrestRecord)\
                    .distinct(ArrestInfo.arrestRecordFKey)\
                    .filter(and_(ArrestInfo.group == label,
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .subquery()
            
                query = s.query(subq.c.tag, func.count(subq.c.group))\
                    .group_by(subq.c.tag)\
                    .order_by(desc(func.count(subq.c.group)))\
                    .all()

                averageAge = getAverageAge(s, ArrestInfo.group, label, activeDays, activeGenders, activeTimes)
                
                genderSubQuery = getGenderSubQuery(s, ArrestInfo.group, label, activeDays, activeGenders, activeTimes)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.group))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.group)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestInfo.group, label, activeDays, activeGenders, activeTimes)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Relevant Tags', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['tags', 'genders', 'days']
                tagColors = [i['color'] for j in query for i in filtersDict if label == i['group']]
                colors = [tagColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == 'tags':
                subq = s.query(ArrestInfo.tag, ArrestInfo.arrest, ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .distinct(ArrestInfo.arrestRecordFKey)\
                    .filter(and_(ArrestInfo.tag == label,
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .subquery()
                query = s.query(subq.c.arrest, func.count(subq.c.tag), subq.c.group)\
                    .group_by(subq.c.arrest, subq.c.tag, subq.c.group)\
                    .order_by(desc(func.count(subq.c.tag)))\
                    .limit(10)\
                    .all()

                group = s.query(ArrestInfo.group)\
                    .filter(ArrestInfo.tag == label)\
                    .limit(1)\
                    .all()[0][0]

                averageAge = getAverageAge(s, ArrestInfo.tag, label, activeDays, activeGenders, activeTimes)

                genderSubQuery = getGenderSubQuery(s, ArrestInfo.tag, label, activeDays, activeGenders, activeTimes)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.tag))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.tag)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestInfo.tag, label, activeDays, activeGenders, activeTimes)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = [f'Top {len(query)} Arrests Belonging to {label}', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == 'arrests':
                subqForJoin = s.query(ArrestInfo.arrestRecordFKey)\
                    .filter(ArrestInfo.arrest == label)\
                    .subquery()

                subq = s.query(ArrestInfo.arrest, ArrestInfo.group)\
                    .join(subqForJoin, ArrestInfo.arrestRecordFKey == subqForJoin.c.arrestRecordFKey)\
                    .join(ArrestRecord)\
                    .filter(and_(ArrestInfo.arrest != label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .subquery()

                query = s.query(subq.c.arrest, func.count(subq.c.arrest), subq.c.group)\
                    .group_by(subq.c.arrest, subq.c.group)\
                    .order_by(desc(func.count(subq.c.arrest)))\
                    .limit(5)\
                    .all()

                tag = s.query(ArrestInfo.tag)\
                    .filter(ArrestInfo.arrest == label)\
                    .limit(1)\
                    .all()[0][0]

                group = s.query(ArrestInfo.group)\
                    .filter(ArrestInfo.arrest == label)\
                    .limit(1)\
                    .all()[0][0]

                averageAge = getAverageAge(s, ArrestInfo.arrest, label, activeDays, activeGenders, activeTimes)

                genderSubQuery = getGenderSubQuery(s, ArrestInfo.arrest, label, activeDays, activeGenders, activeTimes)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.arrest))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.arrest)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestInfo.arrest, label, activeDays, activeGenders, activeTimes)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Associated Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                print(arrestColors)
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == 'ages':
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.age == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(10)\
                    .all()

                genderSubQuery = getGenderSubQuery(s, ArrestRecord.age, label, activeDays, activeGenders, activeTimes)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.age))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.age)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestRecord.age, label, activeDays, activeGenders, activeTimes)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == "dates":
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.date == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(5)\
                    .all()

                averageAge = getAverageAge(s, ArrestRecord.date, label, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo)
                
                genderSubQuery = getGenderSubQuery(s, ArrestRecord.date, label, activeDays, activeGenders, activeTimes)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.date))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.date)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestRecord.date, label, activeDays, activeGenders, activeTimes)
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == "genders":
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.sex == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(10)\
                    .all()

                averageAge = getAverageAge(s, ArrestRecord.sex, label, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo)
                
                daysSubQuery = getDaysSubQuery(s, ArrestRecord.sex, label, activeDays, activeGenders, activeTimes)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in daysQuery]]
                actives = ['arrests', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == "times":
                hour = label.partition(':')[0] + ':'
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.time.contains(hour), ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(5)\
                    .all()
                print(query)

                averageAge = getAverageAge(s, ArrestRecord.time, hour, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo)

                genderSubQuery = getGenderSubQuery(s, ArrestRecord.time, hour, activeDays, activeGenders, activeTimes)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.sex))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.sex)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestRecord.time, hour, activeDays, activeGenders, activeTimes)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == "days":
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.dayOfTheWeek == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(10)\
                    .all()

                averageAge = getAverageAge(s, ArrestRecord.dayOfTheWeek, label, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo)
                
                genderSubQuery = getGenderSubQuery(s, ArrestRecord.dayOfTheWeek, label, activeDays, activeGenders, activeTimes)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.dayOfTheWeek))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 10 Relevant Arrests', 'Gender Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery]]
                actives = ['arrests', 'genders']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery]]
            elif activeBars == "months":
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.timeOfYear == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(10)\
                    .all()

                averageAge = getAverageAge(s, ArrestRecord.timeOfYear, label, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo)
                
                genderSubQuery = getGenderSubQuery(s, ArrestRecord.timeOfYear, label, activeDays, activeGenders, activeTimes)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.timeOfYear))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.timeOfYear)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestRecord.timeOfYear, label, activeDays, activeGenders, activeTimes)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]

        elif queryType == 'charges':
            if activeBars == 'groups':
                subq = s.query(ArrestInfo.group, ArrestInfo.tag)\
                    .join(ArrestRecord)\
                    .filter(and_(ArrestInfo.group == label,
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .subquery()
            
                query = s.query(subq.c.tag, func.count(subq.c.group))\
                    .group_by(subq.c.tag)\
                    .order_by(desc(func.count(subq.c.group)))\
                    .all()

                averageAge = getAverageAge(s, ArrestInfo.group, label, activeDays, activeGenders, activeTimes, _charges = True)
                
                genderSubQuery = getGenderSubQuery(s, ArrestInfo.group, label, activeDays, activeGenders, activeTimes, _charges = True)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.group))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.group)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestInfo.group, label, activeDays, activeGenders, activeTimes, _charges=True)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Relevant Tags', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['tags', 'genders', 'days']
                tagColors = [i['color'] for j in query for i in filtersDict if label == i['group']]
                colors = [tagColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == 'tags':
                subq = s.query(ArrestInfo.tag, ArrestInfo.arrest, ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .filter(and_(ArrestInfo.tag == label,
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .subquery()

                query = s.query(subq.c.arrest, func.count(subq.c.tag), subq.c.group)\
                    .group_by(subq.c.arrest, subq.c.tag, subq.c.group)\
                    .order_by(desc(func.count(subq.c.tag)))\
                    .limit(10)\
                    .all()

                group = s.query(ArrestInfo.group)\
                    .filter(ArrestInfo.tag == label)\
                    .limit(1)\
                    .all()[0][0]

                averageAge = getAverageAge(s, ArrestInfo.tag, label, activeDays, activeGenders, activeTimes, _charges = True)

                genderSubQuery = getGenderSubQuery(s, ArrestInfo.tag, label, activeDays, activeGenders, activeTimes, _charges = True)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.tag))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.tag)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestInfo.tag, label, activeDays, activeGenders, activeTimes, _charges = True)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = [f'Top {len(query)} Arrests Belonging to {label}', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == 'arrests':
                subqForJoin = s.query(ArrestInfo.arrestRecordFKey)\
                    .filter(ArrestInfo.arrest == label)\
                    .subquery()

                subq = s.query(ArrestInfo.arrest, ArrestInfo.group)\
                    .join(subqForJoin, ArrestInfo.arrestRecordFKey == subqForJoin.c.arrestRecordFKey)\
                    .join(ArrestRecord)\
                    .filter(and_(ArrestInfo.arrest != label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .subquery()

                query = s.query(subq.c.arrest, func.count(subq.c.arrest), subq.c.group)\
                    .group_by(subq.c.arrest, subq.c.group)\
                    .order_by(desc(func.count(subq.c.arrest)))\
                    .limit(5)\
                    .all()

                tag = s.query(ArrestInfo.tag)\
                    .filter(ArrestInfo.arrest == label)\
                    .limit(1)\
                    .all()[0][0]

                group = s.query(ArrestInfo.group)\
                    .filter(ArrestInfo.arrest == label)\
                    .limit(1)\
                    .all()[0][0]

                averageAge = getAverageAge(s, ArrestInfo.arrest, label, activeDays, activeGenders, activeTimes, _charges = True)

                genderSubQuery = getGenderSubQuery(s, ArrestInfo.arrest, label, activeDays, activeGenders, activeTimes, _charges = True)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.arrest))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.arrest)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestInfo.arrest, label, activeDays, activeGenders, activeTimes, _charges = True)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Associated Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                print(arrestColors)
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == 'ages':
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.age == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(10)\
                    .all()

                genderSubQuery = getGenderSubQuery(s, ArrestRecord.age, label, activeDays, activeGenders, activeTimes, _charges = True)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.age))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.age)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestRecord.age, label, activeDays, activeGenders, activeTimes, _charges = True)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == "dates":
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.date == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(5)\
                    .all()

                averageAge = getAverageAge(s, ArrestRecord.date, label, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo, _charges = True)
                
                genderSubQuery = getGenderSubQuery(s, ArrestRecord.date, label, activeDays, activeGenders, activeTimes, _charges = True)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.date))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.date)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestRecord.date, label, activeDays, activeGenders, activeTimes, _charges = True)
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == "genders":
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.sex == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(10)\
                    .all()

                averageAge = getAverageAge(s, ArrestRecord.sex, label, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo, _charges = True)
                
                daysSubQuery = getDaysSubQuery(s, ArrestRecord.sex, label, activeDays, activeGenders, activeTimes, _charges = True)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in daysQuery]]
                actives = ['arrests', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == "times":
                hour = label.partition(':')[0] + ':'
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.time.contains(hour), ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(5)\
                    .all()
                print(query)

                averageAge = getAverageAge(s, ArrestRecord.time, hour, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo, _charges = True)

                genderSubQuery = getGenderSubQuery(s, ArrestRecord.time, hour, activeDays, activeGenders, activeTimes, _charges = True)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.sex))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.sex)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestRecord.time, hour, activeDays, activeGenders, activeTimes, _charges = True)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
            elif activeBars == "days":
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.dayOfTheWeek == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(10)\
                    .all()

                averageAge = getAverageAge(s, ArrestRecord.dayOfTheWeek, label, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo, _charges = True)
                
                genderSubQuery = getGenderSubQuery(s, ArrestRecord.dayOfTheWeek, label, activeDays, activeGenders, activeTimes, _charges = True)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.dayOfTheWeek))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 10 Relevant Arrests', 'Gender Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery]]
                actives = ['arrests', 'genders']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery]]
            elif activeBars == "months":
                query = s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .group_by(ArrestInfo.arrest, ArrestInfo.group)\
                    .order_by(desc(func.count(ArrestInfo.arrest)))\
                    .filter(and_(ArrestRecord.timeOfYear == label, ArrestInfo.arrest != 'No arrests listed.',
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .limit(10)\
                    .all()

                averageAge = getAverageAge(s, ArrestRecord.timeOfYear, label, activeDays, activeGenders, activeTimes, _joinTable=ArrestInfo, _charges = True)
                
                genderSubQuery = getGenderSubQuery(s, ArrestRecord.timeOfYear, label, activeDays, activeGenders, activeTimes, _charges = True)

                genderQuery = s.query(genderSubQuery.c.sex, func.count(genderSubQuery.c.timeOfYear))\
                    .group_by(genderSubQuery.c.sex)\
                    .order_by(desc(func.count(genderSubQuery.c.timeOfYear)))\
                    .all()

                daysSubQuery = getDaysSubQuery(s, ArrestRecord.timeOfYear, label, activeDays, activeGenders, activeTimes, _charges = True)
                
                daysQuery = s.query(daysSubQuery.c.dayOfTheWeek, func.count(daysSubQuery.c.dayOfTheWeek))\
                    .group_by(daysSubQuery.c.dayOfTheWeek)\
                    .order_by(desc(func.count(daysSubQuery.c.dayOfTheWeek)))\
                    .all()

                print(query)
                titles = ['Top 5 Relevant Arrests', 'Gender Data', 'Week Data']
                labels = [[i[0] for i in query], [i[0] for i in genderQuery], [i[0] for i in daysQuery]]
                counts = [[i[1] for i in query], [i[1] for i in genderQuery], [i[1] for i in daysQuery]]
                actives = ['arrests', 'genders', 'days']
                arrestColors = [i['color'] for j in query for i in filtersDict if j[2] == i['group']]
                colors = [arrestColors, [colorDict['genders'][i[0]] for i in genderQuery], [colorDict['days'][i[0]] for i in daysQuery]]
    return titles, labels, counts, colors, group, tag, averageAge, actives

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/maps')
def maps():
    return render_template('maps.html')

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/api/maps/calendar')
def minMaxDate():
    query = SQL.select([wichitaArrests])
    result = conn.execute(query)
    existingDates = list(set([row['date'] for row in result]))
    existingDates.sort(key = lambda date: datetime.strptime(date, '%m/%d/%Y'))
    dates = { 'min' : existingDates[0], 'max' : existingDates[-1] }
    return jsonify(dates)

@app.route('/api/maps/<date>')
def returnData(date=None):
    query = SQL.select([wichitaArrests])
    result = conn.execute(query)
    existingDates = list(set([row['date'] for row in result]))
    existingDates.sort()

    if date is None:
        query = SQL.select([wichitaArrests]).where(wichitaArrests.c.date == existingDates[-1])
        result = conn.execute(query)
    else:
        date = date.replace('-', '/')
        startDate, endDate = date.split('+')
        
        if 'null' in startDate and 'null' in endDate:
            startDate = existingDates[-3]
            endDate = existingDates[-1]
        elif 'null' in startDate:
            startDate = endDate
        elif 'null' in endDate:
            endDate = startDate
        
        startIndex = existingDates.index(startDate)
        endIndex = existingDates.index(endDate)
        queryList = existingDates[startIndex:endIndex + 1]

    # i exists solely to seperate duplicate addresses on the map
    i = 0
    addresses = []
    data = []
    result = []
    rows = []
    courthouses = ['455 N MAIN', '141 W ELM']

    for queryDate in queryList:
        query = SQL.select([wichitaArrests]).where(wichitaArrests.c.date == queryDate)
        result = conn.execute(query)
        rows.extend([row for row in result])

    if not DEV_MODE and len(rows) > MAX_ARRESTS:
        print('Requesting more than', MAX_ARRESTS, 'arrests! -', len(rows))
        rows = rows[-MAX_ARRESTS:] 

    for row in rows:
        if row['address'] in addresses:
            i = 0.000015 * addresses.count(row['address'])
        else:
            i = 0

        addresses.append(row['address'])

        courthouse = False
        if row['address'] in courthouses:
            courthouse = True

        data.append(
            {
                'lat' : row['lat'] + i, 
                'lng' : row['lng'],
                'identifier': row['identifier'],
                'courthouse': courthouse,
                'info' : {
                    'address': row['censoredAddress'],
                    'date': row['date'],
                    'time': row['time'],
                    'arrests': row['arrests'],
                    'incidents': row['incidents'],
                    'warrants': row['warrants'],
                    'tags' : row['tags']
                }
            }
        )

    return jsonify(data)

@app.route('/api/stats/sort/<sortMethod>', methods=['GET', 'POST'])
def sortData(sortMethod=None):
    sortType, _, order = sortMethod.partition('-')
    data = request.get_json()

    ascending = True if order == 'ascending' else False

    # Unpack JSON
    numbers = data['data']['numbers']
    labels = data['data']['labels']
    colors = data['data']['colors']
    barsActive = data['activeData']['barsActive']
    groupingActive = data['activeData']['groupingActive']
    dayDataNumbers = data['data']['dayData']['numbers']
    timeDataNumbers = data['data']['timeData']['numbers']
    genderDataNumbers = data['data']['genderData']['numbers']
    ageDataNumbers = data['data']['ageData']['numbers']

    if sortType == 'alpha' and barsActive == 'ages':
        labels = [int(i) for i in labels]
    elif sortType == 'alpha' and barsActive == 'dates':
        labels = [datetime.strptime(date, '%m/%d/%Y') for date in labels]
    
    if sortType == 'numeric':
        if groupingActive == "ages":
            sortedZip = sorted(zip(numbers, labels, colors, dayDataNumbers,
                timeDataNumbers, genderDataNumbers, ageDataNumbers), key=itemgetter(6), reverse=ascending)
        else:
            sortedZip = sorted(zip(numbers, labels, colors, dayDataNumbers,
                timeDataNumbers, genderDataNumbers, ageDataNumbers), reverse=ascending)
    elif sortType == 'alpha':
        sortedZip = sorted(zip(numbers, labels, colors, dayDataNumbers,
                timeDataNumbers, genderDataNumbers, ageDataNumbers), key=itemgetter(1), reverse=ascending)
    
    numbers, labels, colors, dayDataNumbers, \
        timeDataNumbers, genderDataNumbers, ageDataNumbers = zip(*sortedZip)

    if sortType == 'alpha' and barsActive == 'dates':
        labels = [datetime.strftime(date, '%m/%d/%Y') for date in labels]

    data = {
        'numbers': numbers,
        'labels': labels,
        'colors' : colors,
        'genderData': {
            'numbers': genderDataNumbers
        },
        'ageData': {
            'numbers' : ageDataNumbers
        },
        'timeData': {
            'numbers': timeDataNumbers
        },
        'dayData': {
            'numbers': dayDataNumbers
        }
    }
    return jsonify(data)

@app.route('/api/stats/genders/<queryType>')
def statsGenderData(queryType=None):    
    ages, counts, colors = getGenders(queryType)
    data = { 
        'numbers': counts,
        'labels': ages,
        'colors' : colors
    }

    return jsonify(data)

@app.route('/api/stats/months/<queryType>')
def statsMonthsData(queryType=None):    
    ages, counts, colors = getMonths(queryType)
    data = { 
        'numbers': counts,
        'labels': ages,
        'colors' : colors
    }

    return jsonify(data)

@app.route('/api/stats/days/<queryType>')
def statsDaysData(queryType=None):    
    days, counts, colors = getDays(queryType)
    data = { 
        'numbers': counts,
        'labels': days,
        'colors' : colors
    }

    return jsonify(data)

@app.route('/api/stats/times/<queryType>')
def statsTimesData(queryType=None):    
    ages, counts, colors = getTimes(queryType)
    data = { 
        'numbers': counts,
        'labels': ages,
        'colors' : colors
    }

    return jsonify(data)

@app.route('/api/stats/ages/<queryType>')
def statsAgesData(queryType=None):
    ages, counts, colors = getAges(queryType)
    data = { 
        'numbers': counts,
        'labels': ages,
        'colors' : colors
    }
    return jsonify(data)

@app.route('/api/stats/arrests/<queryType>')
def statsArrestsData(queryType=None):
    arrests, counts, colors = getArrests()
    data = { 
        'numbers': counts,
        'labels': arrests,
        'colors' : colors
    }
    return jsonify(data)

@app.route('/api/stats/tags/<queryType>')
def statsTagsData(queryType=None):
    tags, counts, colors = getTags(queryType)

    data = { 
        'numbers': counts,
        'labels': tags,
        'colors' : colors
    }
    return jsonify(data)

@app.route('/api/stats/dates/<queryType>')
def statsDatesData(queryType=None):
    dates, counts, colors = getDatesData(queryType)
    data = { 
        'numbers': counts,
        'labels': dates,
        'colors' : colors
    }
    return jsonify(data)

@app.route('/api/stats/groups/<queryType>')
def statsGroupsData(queryType=None):
    groups, counts, colors = getGroups(queryType)
    data = { 
        'numbers': counts,
        'labels': groups,
        'colors' : colors
    }
    return jsonify(data)

@app.route('/api/stats')
def statsDefaultData():
    tags, counts, colors = getTags()
    data = { 
        'numbers': counts,
        'labels': tags,
        'colors' : colors
    }
    return jsonify(data)

def getSingleLabelCountSubquery(s, _column, _label, _joinTable = ArrestInfo, _charges = False):
    if not _charges:
        if _column != ArrestRecord.time:
            return s.query(_column)\
                .join(_joinTable)\
                .distinct(ArrestInfo.arrestRecordFKey)\
                .group_by(ArrestInfo.arrestRecordFKey, _column)\
                .filter(_column == _label)\
                .subquery()
        else:
            return s.query(_column)\
                .join(_joinTable)\
                .distinct(ArrestInfo.arrestRecordFKey)\
                .group_by(ArrestInfo.arrestRecordFKey, _column)\
                .filter(_column.contains(_label))\
                .subquery()
    else:
        if _column != ArrestRecord.time:
            return s.query(_column)\
                .join(_joinTable)\
                .group_by(_column)\
                .filter(_column == _label)\
                .subquery()
        else:
            return s.query(_column)\
                .join(_joinTable)\
                .group_by(_column)\
                .filter(_column.contains(_label))\
                .subquery()

def getSingleLabelData(_data):
    activeBars = _data['dataActive']
    queryType = _data['queryType']
    label = _data['labels'][0]

    colorDict = {
        'genders': {
            'MALE': '#80d8f2', 
            'FEMALE': '#eb88d4'
        },
        'days': {
            'Sunday': '#FF5500',
            'Monday': '#FF6D00',
            'Tuesday': '#FF8500',
            'Wednesday': '#FF9D00',
            'Thursday': '#FFBC22',
            'Friday': '#FFDB44',
            'Saturday': '#FFFA66'
        },
        'months': {
            "January": "#0095FF",
            "February": "#10A4CC",
            "March": "#20B39A",
            "April": "#30C268",
            "May": "#40D136",
            "June": "#6FC628",
            "July": "#9FBB1B",
            "August": "#CFB00D",
            "September": "#FFA600",
            "October": "#B19B45",
            "November": "#64918B",
            "December": "#1787D1"
        },
        'dates': {
            "01": "#0095FF",
            "02": "#10A4CC",
            "03": "#20B39A",
            "04": "#30C268",
            "05": "#40D136",
            "06": "#6FC628",
            "07": "#9FBB1B",
            "08": "#CFB00D",
            "09": "#FFA600",
            "10": "#B19B45",
            "11": "#64918B",
            "12": "#1787D1"
        }
    }

    timeColors = ["#00044A", "#051553", "#0A275C", "#0F3866", 
        "#144A6F", "#195B78", "#1E6D82", "#237E8B", 
        "#289094", "#2DA19E", "#32B3A7", "#37C4B0", 
        "#3CD6BA", "#36C2AF", "#31AFA5", "#2B9C9B", 
        "#268991", "#207687", "#1B637C", "#155072", 
        "#103D68", "#0A2A5E", "#051754", "#00044A"]

    filtersDict = loadJSON("./static/js/FiltersImproved.json")

    with sessionManager() as s:
        if queryType == 'distinct':
            if activeBars == 'groups':
                subq = getSingleLabelCountSubquery(s, ArrestInfo.group, label, _joinTable=ArrestRecord)
                count = s.query(func.count(subq.c.group))\
                    .all()[0][0]
                color = [i['color'] for i in filtersDict if label == i['group']][0]
            elif activeBars == 'tags':
                subq = getSingleLabelCountSubquery(s, ArrestInfo.tag, label, _joinTable=ArrestRecord)
                count = s.query(func.count(subq.c.tag))\
                    .all()[0][0]
                color = [i['color'] for i in filtersDict if label in i['tags']][0]
            elif activeBars == 'arrests':
                subq = getSingleLabelCountSubquery(s, ArrestInfo.arrest, label, _joinTable=ArrestRecord)
                tag = s.query(ArrestInfo.tag).filter(ArrestInfo.arrest == label).limit(1).all()[0][0]
                count = s.query(func.count(subq.c.arrest))\
                    .all()[0][0]
                color = [i['color'] for i in filtersDict if tag in i['tags']][0]
            elif activeBars == 'ages':
                subq = getSingleLabelCountSubquery(s, ArrestRecord.age, label)
                count = s.query(func.count(subq.c.age))\
                    .all()[0][0]
                color = '#123123'
            elif activeBars == "dates":
                subq = getSingleLabelCountSubquery(s, ArrestRecord.date, label)
                count = s.query(func.count(subq.c.date))\
                    .all()[0][0]
                color = colorDict['dates'][label.partition(' ')[0]]
            elif activeBars == "genders":
                subq = getSingleLabelCountSubquery(s, ArrestRecord.sex, label)
                count = s.query(func.count(subq.c.sex))\
                    .all()[0][0]
                color = colorDict['genders'][label]
            elif activeBars == "times":
                hour = label.partition(':')[0] + ':'
                subq = getSingleLabelCountSubquery(s, ArrestRecord.time, hour)
                count = s.query(func.count(subq.c.time))\
                    .all()[0][0]
                color = timeColors[int(hour[:-1])]
            elif activeBars == "days":
                subq = getSingleLabelCountSubquery(s, ArrestRecord.dayOfTheWeek, label)
                count = s.query(func.count(subq.c.dayOfTheWeek))\
                    .all()[0][0]
                color = colorDict['days'][label]
            elif activeBars == "months":
                subq = getSingleLabelCountSubquery(s, ArrestRecord.timeOfYear, label)
                count = s.query(func.count(subq.c.timeOfYear))\
                    .all()[0][0]
                color = colorDict['months'][label.partition(' ')[0]]

        elif queryType == 'charges':
            # NEED CHARGES
            pass
            
    return count, color

@app.route('/api/stats/label', methods=['GET', 'POST'])
def statsSingleLabelData():
    data = request.get_json()

    count, color = getSingleLabelData(data)

    genderCounts = getGenderData(data)
    averageAgeCounts = getAgeData(data)
    timesCounts = getTimesData(data) 
    daysCounts = getDaysData(data)

    data = {
        'numbers': [count],
        'labels': data['labels'],
        'colors' : [color],
        'genderData': {
            'maleCounts': genderCounts[0],
            'femaleCounts': genderCounts[1]
        },
        'ageData': {
            'averages' : averageAgeCounts
        },
        'timeData': {
            'dayCounts': timesCounts[0],
            'nightCounts': timesCounts[1]
        },
        'dayData': {
            'sundayCounts': daysCounts[0],
            'mondayCounts': daysCounts[1],
            'tuesdayCounts': daysCounts[2],
            'wednesdayCounts': daysCounts[3],
            'thursdayCounts': daysCounts[4],
            'fridayCounts': daysCounts[5],
            'saturdayCounts': daysCounts[6]
        }
    }

    print(data)
    return jsonify(data)

@app.route('/api/stats/hover', methods=['GET', 'POST'])
def statsHoverData():
    data = request.get_json()

    subtitles, sublabels, subnumbers, subcolors, \
        groupInfo, tagInfo, averageAge, actives = getHoverData(data)

    data = {
        'subtitles': subtitles,
        'sublabels' : sublabels,
        'subnumbers' : subnumbers,
        'subcolors' : subcolors,
        'currentLabel' : data['label'],
        'groupInfo' : groupInfo,
        'tagInfo' : tagInfo,
        'averageAge' : averageAge,
        'actives' : actives
    }

    print(data)

    return jsonify(data)

@app.route('/api/stats/grouping/ages', methods=['GET', 'POST'])
def groupAgeData():
    data = request.get_json()

    data = { 
        'ageData' : {
            'numbers': getCountsForGroupingData(data)
        }
    }

    return jsonify(data)

@app.route('/api/stats/grouping/genders', methods=['GET', 'POST'])
def groupGenderData():
    data = request.get_json()
    getQueryData(data)

    data = { 
        'genderData' : {
            'numbers': getCountsForGroupingData(data)
        }
    }

    return jsonify(data)

@app.route('/api/stats/grouping/times', methods=['GET', 'POST'])
def groupTimeData():
    data = request.get_json()

    data = {
        'timeData' : {
            'numbers': getCountsForGroupingData(data)
        }
    }

    return jsonify(data)

@app.route('/api/stats/grouping/days', methods=['GET', 'POST'])
def groupDayData():
    data = request.get_json()

    data = {
        'dayData' : {
            'numbers': getCountsForGroupingData(data)
        }
    }

    return jsonify(data)

    
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
