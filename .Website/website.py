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

def getGroupingData(_s, _queryColumn, _groupingColumn, _label, _joinTable=ArrestRecord, _queryType = 'distinct'):
    # QUERY METHOD NEEDS TO BE DIFFERENT FOR TIME
    # TIMES ARE EXACT AND WOULD MAKE ANALYSIS AWFUL IF DONE UNIQUELY
    if _label:
        initialFilterQuery = and_(_queryColumn != None, _queryColumn == _label)
    else:
        initialFilterQuery = (_queryColumn != None)

    if _queryColumn == ArrestRecord.time:
        dataSubq = _s.query(func.substr(_queryColumn, 0, 4).label('time'))\
            .distinct(func.substr(_queryColumn, 0, 4))\
            .filter(_queryColumn != None)\
            .subquery()
    elif _queryColumn != ArrestRecord.time:
        dataSubq = _s.query(_queryColumn)\
            .distinct(_queryColumn)\
            .filter(initialFilterQuery)\
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

def unzipToList(_zipList):
    return list(map(list, zip(*_zipList)))

def getNumbersFromQuery(_q):
    queryAsList = unzipToList(_q)
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

def getRespectiveColumnString(_column):
    if _column == ArrestInfo.group:
        return "groups"
    elif _column == ArrestInfo.tag:
        return "tags"
    elif _column == ArrestInfo.arrest:
        return "arrests"
    elif _column == ArrestRecord.age:
        return "ages"
    elif _column == ArrestRecord.date:
        return "dates"
    elif _column == ArrestRecord.sex:
        return "genders"
    elif _column == ArrestRecord.time:
        return "times"
    elif _column == ArrestRecord.dayOfTheWeek:
        return "days"
    elif _column == ArrestRecord.timeOfYear:
        return "months"

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

def getCountsForGroupingData(_data):
    active = _data['dataActive']
    queryType = _data['queryType']
    grouping = _data['groupingType']

    try:
        label = _data['label']
    except:
        label = None
    
    queriedColumn = getRespectiveQueryColumn(active)
    groupingColumn = getRespectiveGroupingColumn(grouping)

    with sessionManager() as s:
        if queryType == 'distinct':
            query = getGroupingData(s, queriedColumn, groupingColumn, label, _joinTable=ArrestInfo)
        elif queryType == 'charges':
            query = getGroupingData(s, queriedColumn, groupingColumn, label, _joinTable=ArrestInfo, _queryType = 'charges')
        counts = getNumbersFromQuery(query)
    return counts

def getRespectiveColors(_string, _labels, _supportList = None):
    groupColorsDict = loadJSON("./static/js/FiltersImproved.json")
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
    genderDict = {
        "MALE" : '#80d8f2',
        "FEMALE" :'#eb88d4'
    }
    daysDict = {
        'Sunday': '#FF5500',
        'Monday': '#FF6D00',
        'Tuesday': '#FF8500',
        'Wednesday': '#FF9D00',
        'Thursday': '#FFBC22',
        'Friday': '#FFDB44',
        'Saturday': '#FFFA66'
    }

    if _string == "groups" or _string == 'tags' or _string == 'arrests':
        return [next(i['color'] for i in groupColorsDict if i['group'] == group) for group in _supportList]
    elif _string == "ages":
        return ['#def123'] * len(_labels)
    elif _string == "dates":
        return [dateDict[i.partition('/')[0]] for i in _labels]
    elif _string == "genders":
        return [genderDict[i] for i in _labels]
    elif _string == "times":
        return ["#00044A", "#051553", "#0A275C", "#0F3866", 
            "#144A6F", "#195B78", "#1E6D82", "#237E8B", 
            "#289094", "#2DA19E", "#32B3A7", "#37C4B0", 
            "#3CD6BA", "#36C2AF", "#31AFA5", "#2B9C9B", 
            "#268991", "#207687", "#1B637C", "#155072", 
            "#103D68", "#0A2A5E", "#051754", "#00044A"]
    elif _string == "days":
        return [daysDict[i] for i in _labels]
    elif _string == "months":
        return [monthDict[i.partition(' ')[0]] for i in _labels]

def isGroupColorQuery(_queryColumn):
    return _queryColumn == ArrestInfo.arrest or _queryColumn == ArrestInfo.tag or _queryColumn == ArrestInfo.group

def getQueryData(_data):
    print(_data)
    queryString = _data['dataActive']
    queryColumn = getRespectiveQueryColumn(queryString)
    queryType = _data['queryType']

    try:
        label = _data['label']
    except:
        label = None

    if isGroupColorQuery(queryColumn):
        joinTable = ArrestRecord
    else:
        joinTable = ArrestInfo

    filterQuery = getRespectiveFilter(queryString, queryColumn)
    sortingCase = getRespectiveSortingCase(queryString, queryColumn)

    if label:
        # if there is a label, limit it to that label
        labelQuery = (queryColumn == label)
    else:
        # if there is no label, query as normal
        # this is essentially a duplicate of the filterQuery
        # duplicating keeps this function modular
        labelQuery = (queryColumn != None)

    with sessionManager() as s:
        if queryType == 'charges':
            if isGroupColorQuery(queryColumn):
                query = s.query(queryColumn, func.count(queryColumn).label('count'),
                        ArrestInfo.group)\
                    .join(joinTable)\
                    .filter(and_(filterQuery, labelQuery))\
                    .order_by(sortingCase)\
                    .group_by(queryColumn, ArrestInfo.group)\
                    .all()
            elif queryString == "times":
                trimmedTimeColumn = func.substr(queryColumn, 0, 4)
                query = s.query(trimmedTimeColumn, 
                    func.count(trimmedTimeColumn).label('count'))\
                    .join(joinTable)\
                    .filter(and_(filterQuery, labelQuery))\
                    .order_by(trimmedTimeColumn)\
                    .group_by(trimmedTimeColumn)\
                    .all()
            else:
                query = s.query(queryColumn, func.count(queryColumn).label('count'))\
                    .join(joinTable)\
                    .filter(and_(filterQuery, labelQuery))\
                    .order_by(sortingCase)\
                    .group_by(queryColumn)\
                    .all()
        elif queryType == 'distinct':
            if queryString == "times":
                distinctQuerySubq = s.query(func.substr(queryColumn, 0, 4).label('time'), ArrestInfo.group)\
                    .join(joinTable)\
                    .distinct(ArrestRecord.recordID, func.substr(queryColumn, 0, 4))\
                    .filter(and_(filterQuery, labelQuery))\
                    .group_by(ArrestRecord.recordID, func.substr(queryColumn, 0, 4), ArrestInfo.group)\
                    .subquery()
            else:
                distinctQuerySubq = s.query(queryColumn, ArrestInfo.group)\
                    .join(joinTable)\
                    .distinct(ArrestRecord.recordID, queryColumn)\
                    .filter(and_(filterQuery, labelQuery))\
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

    if queryColumn == ArrestRecord.timeOfYear:
        query = sorted(query, key=lambda x: datetime.strptime(x[0], '%B %Y'))

    try:
        labels, counts = unzipToList(query)
        if queryString == 'dates':
            labels = [date.strftime(i[0], "%m/%d/%Y") for i in query]
        elif queryString == 'times':
            labels = [hour[0] + '00 - ' + hour[0] + '59' for hour in query]
        colors = getRespectiveColors(queryString, labels)
    except ValueError:
        labels, counts, supportGroups = unzipToList(query)
        colors = getRespectiveColors(queryString, labels, _supportList=supportGroups)
        
    return labels, counts, colors

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

@app.route('/api/stats/queriedData', methods=['GET', 'POST'])
def statsQueriedData():
    data = request.get_json()
    labels, counts, colors = getQueryData(data)
    print('DEBUG: QUERY CALLED')
    data = { 
        'labels': labels,
        'numbers': counts,
        'colors' : colors
    }
    return data

@app.route('/api/stats/label', methods=['GET', 'POST'])
def statsSingleLabelData():
    data = request.get_json()
    label, count, color = getQueryData(data)
    
    # Not happy with using a loop here, but it works and saves tons of lines
    # Might be able to shoehorn a solution into the frontend?
    groupings = ['genders', 'ages', 'times', 'days']
    groupingData = []
    for i in groupings:
        data['groupingType'] = i
        groupingData.append(getCountsForGroupingData(data))
    
    data = {
        'numbers': count,
        'colors' : color,
        'genderData': {
            'numbers' : groupingData[0]
        },
        'ageData': {
            'numbers' : groupingData[1]
        },
        'timeData': {
            'numbers' : groupingData[2]
        },
        'dayData': {
            'numbers' : groupingData[3]
        }
    }

    return jsonify(data)

def getSelectedArrests(_s, _queryColumn, _queryFilter, _queryType, _label, n=10):
    if _queryType == 'distinct':
        subq = _s.query(ArrestInfo.arrest, ArrestInfo.group)\
            .join(ArrestRecord)\
            .distinct(ArrestRecord.recordID)\
            .filter(_queryFilter)\
            .group_by(ArrestRecord.recordID, ArrestInfo.arrest, ArrestInfo.group)\
            .subquery()

        return _s.query(subq.c.arrest, func.count(subq.c.arrest), subq.c.group)\
                .group_by(subq.c.arrest, subq.c.group)\
                .order_by(desc(func.count(subq.c.arrest)))\
                .limit(n)\
                .all()
    else:
        return _s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
            .join(ArrestRecord)\
            .group_by(ArrestInfo.arrest, ArrestInfo.group)\
            .order_by(desc(func.count(ArrestInfo.arrest)))\
            .filter(_queryFilter)\
            .limit(n)\
            .all()

def getRelatedArrests(_s, _label, n=5):
    # don't need to have a distinct here, as arrests are inherently distinct
    subq = _s.query(ArrestInfo.arrestRecordFKey.label("ID"))\
            .filter(ArrestInfo.arrest == _label)\
            .subquery()
    # literal is needed here to align with getSelectedArrests query format
    return _s.query(ArrestInfo.arrest, func.count(ArrestInfo.arrest), ArrestInfo.group)\
            .join(subq, subq.c.ID == ArrestInfo.arrestRecordFKey)\
            .filter(and_(ArrestInfo.arrest != _label, 
                ArrestInfo.arrest != None, 
                ArrestInfo != 'No arrests listed.'))\
            .group_by(ArrestInfo.arrest, ArrestInfo.group)\
            .order_by(desc(func.count(ArrestInfo.arrest)))\
            .limit(n)\
            .all()

def getSelectedGrouping(_s, _queryColumn, _groupingColumn, _queryFilter, _queryType):
    if _queryType == 'distinct':
        subq = _s.query(_groupingColumn)\
                .join(ArrestInfo)\
                .distinct(ArrestInfo.arrestRecordFKey)\
                .filter(_queryFilter)\
                .group_by(ArrestInfo.arrestRecordFKey, _groupingColumn)\
                .subquery()

        groupingString = getRespectiveColumnString(_groupingColumn)
        subqGroupingStringColumn = getRespectiveSubqueryColumn(groupingString, subq)

        if _groupingColumn == ArrestRecord.age:
            return _s.query(cast(func.avg(subqGroupingStringColumn), Float))\
                .all()
        else:
            return _s.query(subqGroupingStringColumn, func.count(subqGroupingStringColumn))\
                .group_by(subqGroupingStringColumn)\
                .order_by(desc(func.count(subqGroupingStringColumn)))\
                .all()
    else:
        if _groupingColumn == ArrestRecord.age:
            return _s.query(cast(func.avg(_groupingColumn), Float))\
                .join(ArrestInfo)\
                .group_by(_queryColumn)\
                .filter(and_(_queryFilter, _groupingColumn != None))\
                .all()
        else:
            return _s.query(_groupingColumn, func.count(_groupingColumn))\
                .join(ArrestInfo)\
                .group_by(_groupingColumn)\
                .order_by(desc(func.count(_groupingColumn)))\
                .filter(and_(_queryFilter, _groupingColumn != None))\
                .all()

def getRespectiveSelectedActives(_string):
    # don't actually want to filter out arrests so it is kept out
    subactives = ['genders', 'days']
    return ['arrests'] + list(filter(lambda x: x != _string, subactives))

def getRespectiveTitles(_string, _lengthOfArrests):
    if _string == 'arrests':
        return f'Top {_lengthOfArrests} arrests'
    elif _string == 'genders':
        return 'Gender Data'
    elif _string == 'days':
        return 'Age Data'

def removeDeadInfo(_actives, _list):
    if "genders" not in _actives:
        del _list[1]
    elif "days" not in _actives:
        del _list[2]
    return _list

def getSelectedLabelData(_data):
    group = None
    tag = None

    print(_data)
    queryString = _data['activeData']['barsActive']
    queryColumn = getRespectiveQueryColumn(queryString)
    groupingString = _data['activeData']['groupingActive']
    groupingColumn = getRespectiveGroupingColumn(groupingString)

    queryType = _data['activeData']['queryType']
    label = _data['label']
    sublabel = _data['sublabel']

    if queryString == 'times':
        label = label.partition(':')[0] + ":"
        likeString = '{}%'.format(label)
        labelFilter = (queryColumn.like(likeString))
    else:
        labelFilter = (queryColumn == label)

    if groupingColumn:
        groupingFilter = (groupingColumn.in_((sublabel, )))
        queryFilter = and_(labelFilter, groupingFilter)
    else:
        queryFilter = labelFilter

    with sessionManager() as s:
        if queryString in ['arrests', 'tags']:
            group = s.query(ArrestInfo.group)\
                .filter(queryFilter)\
                .limit(1)\
                .all()[0][0]

        if queryColumn == ArrestInfo.arrest:
            arrestGrouping = getRelatedArrests(s, label)
            tag = s.query(ArrestInfo.tag)\
                .filter(queryFilter)\
                .limit(1)\
                .all()[0][0]
        else:
            arrestGrouping = getSelectedArrests(s, queryColumn, queryFilter, queryType, label)
        groupColors = [i[2] for i in arrestGrouping]
        genderGrouping = getSelectedGrouping(s, queryColumn, ArrestRecord.sex, queryFilter, queryType)
        dayGrouping = getSelectedGrouping(s, queryColumn, ArrestRecord.dayOfTheWeek, queryFilter, queryType)
        ageGrouping = getSelectedGrouping(s, queryColumn, ArrestRecord.age, queryFilter, queryType)

    averageAge = round(ageGrouping[0][0], 2)
    actives = getRespectiveSelectedActives(queryString)
    titles = [getRespectiveTitles(i, len(arrestGrouping)) for i in actives]

    if queryColumn == ArrestInfo.arrest:
        titles[0] = f'Top {len(arrestGrouping)} Associated Arrests'
    
    initialLabels = [[i[0] for i in arrestGrouping], [i[0] for i in genderGrouping], [i[0] for i in dayGrouping]]
    initialCounts = [[i[1] for i in arrestGrouping], [i[1] for i in genderGrouping], [i[1] for i in dayGrouping]]
    labels = removeDeadInfo(actives, initialLabels)
    counts = removeDeadInfo(actives, initialCounts)
    colors = [getRespectiveColors(e, labels[i], groupColors) for i, e in enumerate(actives)]
    
    # Warrants are viewed differently in the database
    if label == 'Warrants':
        del titles[0]
        del labels[0]
        del counts[0]
        del colors[0]
        del actives[0]
    
    return titles, labels, counts, colors, group, tag, averageAge, actives

@app.route('/api/stats/hover', methods=['GET', 'POST'])
def statsHoverData():
    data = request.get_json()

    subtitles, sublabels, subnumbers, subcolors, \
        groupInfo, tagInfo, averageAge, actives = getSelectedLabelData(data)

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

    return jsonify(data)

def getRespectiveDataTypeForJSON(_string):
    if _string == "ages":
        return "ageData"
    elif _string == "genders":
        return "genderData"
    elif _string == "days":
        return "dayData"
    elif _string == "times":
        return "timeData"

@app.route('/api/stats/grouping', methods=['GET', 'POST'])
def groupData():
    data = request.get_json()
    dataType = getRespectiveDataTypeForJSON(data['groupingType'])

    data = { 
        dataType : {
            'numbers': getCountsForGroupingData(data)
        }
    }

    return jsonify(data)
    
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
