from flask import Flask, url_for, render_template, jsonify, request
from operator import itemgetter
from datetime import datetime, timedelta, date
import json, random, itertools, os
import sqlalchemy as SQL
from sqlalchemy import create_engine, func, and_, or_, desc
from sqlalchemy.types import Integer, Date, Float
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import cast
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

def getAgeData(_data):
    active = _data['dataActive']
    queryType = _data['queryType']
    labels = _data['labels']

    with sessionManager() as s:
        if queryType == "distinct":
            if active == "groups":
                subquery = s.query(ArrestInfo.group, ArrestRecord.age)\
                    .join(ArrestInfo)\
                    .distinct(ArrestRecord.recordID, ArrestInfo.group)\
                    .group_by(ArrestRecord.recordID, ArrestInfo.group)\
                    .subquery()

                ageCounts = [s.query(cast(func.avg(subquery.c.age), Float))\
                    .filter(subquery.c.group == label)\
                    .all()[0][0] for label in labels]
            elif active == "tags":
                subquery = s.query(ArrestInfo.tag, ArrestRecord.age)\
                    .join(ArrestInfo)\
                    .distinct(ArrestRecord.recordID, ArrestInfo.tag)\
                    .group_by(ArrestRecord.recordID, ArrestInfo.tag)\
                    .subquery()

                ageCounts = [s.query(cast(func.avg(subquery.c.age), Float))\
                    .filter(subquery.c.tag == label)\
                    .all()[0][0] for label in labels]
            elif active == "arrests":
                subquery = s.query(ArrestInfo.arrest, ArrestRecord.age)\
                    .join(ArrestInfo)\
                    .subquery()

                ageCounts = [s.query(cast(func.avg(subquery.c.age), Float))\
                    .filter(subquery.c.arrest == label)\
                    .all()[0][0] for label in labels]
            elif active == "ages":
                ageCounts = [int(i) for i in labels]
            elif active == "dates":
                ageCounts = [s.query(cast(func.avg(ArrestRecord.age), Float))\
                    .filter(ArrestRecord.date == label)\
                    .all()[0][0] for label in labels]
            elif active == "genders":
                ageCounts = [s.query(cast(func.avg(ArrestRecord.age), Float))\
                    .filter(ArrestRecord.sex == label)\
                    .all()[0][0] for label in labels]
            elif active == "times":
                hours = [int(label.partition(':')[0]) for label in labels]
                labels = [str(x) + ':' if x >= 10 else '0' + str(x) + ':' for x in hours]
                ageCounts = [s.query(cast(func.avg(ArrestRecord.age), Float))\
                    .filter(ArrestRecord.time.contains(label))\
                    .all()[0][0] for label in labels]
            elif active == "days":
                ageCounts = [s.query(cast(func.avg(ArrestRecord.age), Float))\
                    .filter(ArrestRecord.dayOfTheWeek == label)\
                    .all()[0][0] for label in labels]
            elif active == "months":
                ageCounts = [s.query(cast(func.avg(ArrestRecord.age), Float))\
                    .filter(ArrestRecord.timeOfYear == label)\
                    .all()[0][0] for label in labels]
        elif queryType == "charges":
            if active == "groups":
                ageCounts = [float(s.query(func.avg(ArrestRecord.age))\
                    .join(ArrestInfo)\
                    .filter(ArrestInfo.group == label)\
                    .all()[0][0]) for label in labels]
            elif active == "tags":
                ageCounts = [float(s.query(func.avg(ArrestRecord.age))\
                    .join(ArrestInfo)\
                    .filter(ArrestInfo.tag == label)\
                    .all()[0][0]) for label in labels]
            elif active == "arrests":
                ageCounts = [float(s.query(func.avg(ArrestRecord.age))\
                    .join(ArrestInfo)\
                    .filter(ArrestInfo.arrest == label)\
                    .all()[0][0]) for label in labels]
            elif active == "ages":
                ageCounts = [int(i) for i in labels]
            elif active == "dates":
                ageCounts = [s.query(cast(func.avg(ArrestRecord.age), Float))\
                    .join(ArrestInfo)\
                    .filter(ArrestRecord.date == label)\
                    .all()[0][0] for label in labels]
            elif active == "genders":
                ageCounts = [float(s.query(func.avg(ArrestRecord.age))\
                    .join(ArrestInfo)\
                    .filter(ArrestRecord.sex == label)\
                    .all()[0][0]) for label in labels]
            elif active == "times":
                hours = [int(label.partition(':')[0]) for label in labels]
                labels = [str(x) + ':' if x >= 10 else '0' + str(x) + ':' for x in hours]
                ageCounts = [float(s.query(func.avg(ArrestRecord.age))\
                    .join(ArrestInfo)\
                    .filter(ArrestRecord.time.contains(label))\
                    .all()[0][0]) for label in labels]
            elif active == "days":
                ageCounts = [float(s.query(func.avg(ArrestRecord.age))\
                    .join(ArrestInfo)\
                    .filter(ArrestRecord.dayOfTheWeek == label)\
                    .all()[0][0]) for label in labels]
            elif active == "months":
                ageCounts = [float(s.query(func.avg(ArrestRecord.age))\
                    .join(ArrestInfo)\
                    .filter(ArrestRecord.timeOfYear == label)\
                    .all()[0][0]) for label in labels]

    return ageCounts

# DISTINCT. IDEA IS THAT THE GROUP LIES WITHIN THE CHARGE. DUPLICATES ARE NOT COUNTED
#genderCounts = [[s.query(ArrestRecord.recordID, ArrestInfo.group)\
    #.join(ArrestInfo)\
    #.distinct(ArrestRecord.recordID, ArrestInfo.group)\
    #.filter(and_(ArrestRecord.sex == sex, ArrestInfo.group == label))\
    #.count() for label in labels] for sex in sexes]

def getGenderData(_data):
    active = _data['dataActive']
    queryType = _data['queryType']
    labels = _data['labels']
    sexes = ["MALE", "FEMALE"]

    with sessionManager() as s:
        if queryType == "distinct":
            if active == "groups":
                genderCounts = [[s.query(ArrestRecord.recordID, ArrestInfo.group)\
                    .join(ArrestInfo)\
                    .distinct(ArrestRecord.recordID, ArrestInfo.group)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestInfo.group == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "tags":
                genderCounts = [[s.query(ArrestRecord.recordID, ArrestInfo.tag)\
                    .join(ArrestInfo)\
                    .distinct(ArrestRecord.recordID, ArrestInfo.tag)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestInfo.tag == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "arrests":
                genderCounts = [[s.query(ArrestRecord.recordID, ArrestInfo.arrest)\
                    .join(ArrestInfo)\
                    .distinct(ArrestRecord.recordID, ArrestInfo.arrest)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestInfo.arrest == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "ages":
                genderCounts = [[s.query(ArrestRecord.recordID, ArrestRecord.age)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.age == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "dates":
                genderCounts = [[s.query(ArrestRecord.recordID, ArrestRecord.date)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.date == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "genders":
                genderCounts = [[0, 0], [0, 0]]
            elif active == "times":
                hours = [int(label.partition(':')[0]) for label in labels]
                labels = [str(x) + ':' if x >= 10 else '0' + str(x) + ':' for x in hours]
                genderCounts = [[s.query(ArrestRecord.recordID, ArrestRecord.time)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.time.contains(label)))\
                    .count() for label in labels] for sex in sexes]
            elif active == "days":
                genderCounts = [[s.query(ArrestRecord.recordID, ArrestRecord.dayOfTheWeek)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.dayOfTheWeek == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "months":
                genderCounts = [[s.query(ArrestRecord.recordID, ArrestRecord.timeOfYear)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.timeOfYear == label))\
                    .count() for label in labels] for sex in sexes]
        elif queryType == "charges":
            if active == "groups":
                genderCounts = [[s.query(ArrestRecord)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestInfo.group == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "tags":
                genderCounts = [[s.query(ArrestRecord)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestInfo.tag == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "arrests":
                genderCounts = [[s.query(ArrestRecord)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestInfo.arrest == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "ages":
                genderCounts = [[s.query(ArrestRecord)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.age == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "dates":
                genderCounts = [[s.query(ArrestRecord)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.date == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "genders":
                genderCounts = [[0, 0], [0, 0]]
            elif active == "times":
                hours = [int(label.partition(':')[0]) for label in labels]
                labels = [str(x) + ':' if x >= 10 else '0' + str(x) + ':' for x in hours]
                genderCounts = [[s.query(ArrestRecord)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.time.contains(label)))\
                    .count() for label in labels] for sex in sexes]
            elif active == "days":
                genderCounts = [[s.query(ArrestRecord)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.dayOfTheWeek == label))\
                    .count() for label in labels] for sex in sexes]
            elif active == "months":
                genderCounts = [[s.query(ArrestRecord)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.sex == sex, ArrestRecord.timeOfYear == label))\
                    .count() for label in labels] for sex in sexes]
    return genderCounts

def getDaysData(_data):
    active = _data['dataActive']
    queryType = _data['queryType']
    labels = _data['labels']
    
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
    'Thursday', 'Friday', 'Saturday']

    with sessionManager() as s:
        if queryType == 'distinct':
            if active == "groups":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestInfo.group == label))\
                    .distinct(ArrestRecord.recordID, ArrestRecord.dayOfTheWeek, ArrestInfo.group)\
                    .group_by(ArrestRecord.recordID, ArrestRecord.dayOfTheWeek, ArrestInfo.group)\
                    .count() for label in labels] for day in days]
            elif active == "tags":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestInfo.tag == label))\
                    .distinct(ArrestRecord.recordID, ArrestRecord.dayOfTheWeek, ArrestInfo.tag)\
                    .group_by(ArrestRecord.recordID, ArrestRecord.dayOfTheWeek, ArrestInfo.tag)\
                    .count() for label in labels] for day in days]
            elif active == "arrests":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestInfo.arrest == label))\
                    .distinct(ArrestRecord.recordID, ArrestRecord.dayOfTheWeek, ArrestInfo.arrest)\
                    .group_by(ArrestRecord.recordID, ArrestRecord.dayOfTheWeek, ArrestInfo.arrest)\
                    .count() for label in labels] for day in days]
            elif active == "ages":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.age == label))\
                    .count() for label in labels] for day in days]
            elif active == "dates":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.date == label))\
                    .count() for label in labels] for day in days]
            elif active == "genders":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.sex == label))\
                    .count() for label in labels] for day in days]
            elif active == "times":
                hours = [int(label.partition(':')[0]) for label in labels]
                labels = [str(x) + ':' if x >= 10 else '0' + str(x) + ':' for x in hours]
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.time.contains(label)))\
                    .count() for label in labels] for day in days]
            elif active == "days":
                dayCounts = [[0, 0, 0] * 24] * 7
            elif active == "months":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.timeOfYear == label))\
                    .count() for label in labels] for day in days]
        elif queryType == 'charges':
            if active == "groups":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestInfo.group == label))\
                    .count() for label in labels] for day in days]
            elif active == "tags":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestInfo.tag == label))\
                    .count() for label in labels] for day in days]
            elif active == "arrests":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestInfo.arrest == label))\
                    .count() for label in labels] for day in days]
            elif active == "ages":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.age == label))\
                    .count() for label in labels] for day in days]
            elif active == "dates":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.date == label))\
                    .count() for label in labels] for day in days]
            elif active == "genders":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.sex == label))\
                    .count() for label in labels] for day in days]
            elif active == "times":
                hours = [int(label.partition(':')[0]) for label in labels]
                labels = [str(x) + ':' if x >= 10 else '0' + str(x) + ':' for x in hours]
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.time.contains(label)))\
                    .count() for label in labels] for day in days]
            elif active == "days":
                dayCounts = [[0, 0, 0] * 24] * 7
            elif active == "months":
                dayCounts = [[s.query(ArrestRecord.dayOfTheWeek)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.dayOfTheWeek == day, ArrestRecord.timeOfYear == label))\
                    .count() for label in labels] for day in days]
    return dayCounts

def getTimesData(_data):
    active = _data['dataActive']
    queryType = _data['queryType']
    labels = _data['labels']
    times = ['DAY', 'NIGHT']

    with sessionManager() as s:
        if queryType == 'distinct':
            if active == "groups":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestInfo.group == label))\
                    .distinct(ArrestRecord.recordID, ArrestRecord.timeOfDay, ArrestInfo.group)\
                    .group_by(ArrestRecord.recordID, ArrestRecord.timeOfDay, ArrestInfo.group)\
                    .count() for label in labels] for time in times]
            elif active == "tags":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestInfo.tag == label))\
                    .distinct(ArrestRecord.recordID, ArrestRecord.timeOfDay, ArrestInfo.tag)\
                    .group_by(ArrestRecord.recordID, ArrestRecord.timeOfDay, ArrestInfo.tag)\
                    .count() for label in labels] for time in times]
            elif active == "arrests":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestInfo.arrest == label))\
                    .distinct(ArrestRecord.recordID, ArrestRecord.timeOfDay, ArrestInfo.arrest)\
                    .group_by(ArrestRecord.recordID, ArrestRecord.timeOfDay, ArrestInfo.arrest)\
                    .count() for label in labels] for time in times]
            elif active == "ages":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.age == label))\
                    .count() for label in labels] for time in times]
            elif active == "dates":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.date == label))\
                    .count() for label in labels] for time in times]
            elif active == "genders":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.sex == label))\
                    .count() for label in labels] for time in times]
            elif active == "times":
                timeCounts = [[0, 0] * 24] * 2
            elif active == "days":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.dayOfTheWeek == label))\
                    .count() for label in labels] for time in times]
            elif active == "months":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.timeOfYear == label))\
                    .count() for label in labels] for time in times]
        elif queryType == 'charges':
            if active == "groups":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestInfo.group == label))\
                    .count() for label in labels] for time in times]
            elif active == "tags":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestInfo.tag == label))\
                    .count() for label in labels] for time in times]
            elif active == "arrests":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestInfo.arrest == label))\
                    .count() for label in labels] for time in times]
            elif active == "ages":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.age == label))\
                    .count() for label in labels] for time in times]
            elif active == "dates":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.date == label))\
                    .count() for label in labels] for time in times]
            elif active == "genders":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.sex == label))\
                    .count() for label in labels] for time in times]
            elif active == "times":
                timeCounts = [[0, 0] * 24] * 2
            elif active == "days":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.dayOfTheWeek == label))\
                    .count() for label in labels] for time in times]
            elif active == "months":
                timeCounts = [[s.query(ArrestRecord.timeOfDay)\
                    .join(ArrestInfo)\
                    .filter(and_(ArrestRecord.timeOfDay == time, ArrestRecord.timeOfYear == label))\
                    .count() for label in labels] for time in times]
    return timeCounts

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
                print('t1234123est')
                subq = s.query(ArrestInfo.tag, ArrestInfo.arrest, ArrestInfo.group)\
                    .join(ArrestRecord)\
                    .distinct(ArrestInfo.arrestRecordFKey)\
                    .filter(and_(ArrestInfo.tag == label,
                    ArrestRecord.sex.in_(activeGenders),
                    ArrestRecord.timeOfDay.in_(activeTimes),
                    ArrestRecord.dayOfTheWeek.in_(activeDays)))\
                    .subquery()
                print('asdasd')
                query = s.query(subq.c.arrest, func.count(subq.c.tag), subq.c.group)\
                    .group_by(subq.c.arrest, subq.c.tag, subq.c.group)\
                    .order_by(desc(func.count(subq.c.tag)))\
                    .limit(10)\
                    .all()
                print('test')

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
    maleCounts = data['data']['genderData']['maleCounts']
    femaleCounts = data['data']['genderData']['femaleCounts']
    dayCounts = data['data']['timeData']['dayCounts']
    nightCounts = data['data']['timeData']['nightCounts']
    femaleCounts = data['data']['genderData']['femaleCounts']
    averageAges = data['data']['ageData']['averages']
    barsActive = data['activeData']['barsActive']
    groupingActive = data['activeData']['groupingActive']
    sundayCounts = data['data']['dayData']['sundayCounts']
    mondayCounts = data['data']['dayData']['mondayCounts']
    tuesdayCounts = data['data']['dayData']['tuesdayCounts']
    wednesdayCounts = data['data']['dayData']['wednesdayCounts']
    thursdayCounts = data['data']['dayData']['thursdayCounts']
    fridayCounts = data['data']['dayData']['fridayCounts']
    saturdayCounts = data['data']['dayData']['saturdayCounts']

    if sortType == 'alpha' and barsActive == 'ages':
        labels = [int(i) for i in labels]
    elif sortType == 'alpha' and barsActive == 'dates':
        labels = [datetime.strptime(date, '%m/%d/%Y') for date in labels]
    
    if sortType == 'numeric':
        if groupingActive == "ages":
            sortedZip = sorted(zip(numbers, labels, colors, maleCounts, femaleCounts, 
                averageAges, dayCounts, nightCounts, sundayCounts, mondayCounts, 
                tuesdayCounts, wednesdayCounts, thursdayCounts, fridayCounts, saturdayCounts), key=itemgetter(5), reverse=ascending)
        else:
            sortedZip = sorted(zip(numbers, labels, colors, maleCounts, femaleCounts, 
                averageAges, dayCounts, nightCounts, sundayCounts, mondayCounts, 
                tuesdayCounts, wednesdayCounts, thursdayCounts, fridayCounts, saturdayCounts), reverse=ascending)
    elif sortType == 'alpha':
        sortedZip = sorted(zip(numbers, labels, colors, maleCounts, femaleCounts, 
            averageAges, dayCounts, nightCounts, sundayCounts, mondayCounts, 
            tuesdayCounts, wednesdayCounts, thursdayCounts, fridayCounts, saturdayCounts), key=itemgetter(1), reverse=ascending)
    
    numbers, labels, colors, maleCounts, femaleCounts, \
        averageAges, dayCounts, nightCounts, \
        sundayCounts, mondayCounts, tuesdayCounts, wednesdayCounts, \
        thursdayCounts, fridayCounts, saturdayCounts = zip(*sortedZip)

    if sortType == 'alpha' and barsActive == 'dates':
        labels = [datetime.strftime(date, '%m/%d/%Y') for date in labels]

    data = {
        'numbers': numbers,
        'labels': labels,
        'colors' : colors,
        'genderData': {
            'maleCounts': maleCounts,
            'femaleCounts': femaleCounts
        },
        'ageData': {
            'averages' : averageAges
        },
        'timeData': {
            'dayCounts': dayCounts,
            'nightCounts': nightCounts
        },
        'dayData': {
            'sundayCounts': sundayCounts,
            'mondayCounts': mondayCounts,
            'tuesdayCounts': tuesdayCounts,
            'wednesdayCounts': wednesdayCounts,
            'thursdayCounts': thursdayCounts,
            'fridayCounts': fridayCounts,
            'saturdayCounts': saturdayCounts
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
    print(_data)
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
                # NEED COLOR
            elif activeBars == 'tags':
                subq = getSingleLabelCountSubquery(s, ArrestInfo.tag, label, _joinTable=ArrestRecord)
                count = s.query(func.count(subq.c.tag))\
                    .all()[0][0]
                # NEED COLOR
            elif activeBars == 'arrests':
                subq = getSingleLabelCountSubquery(s, ArrestInfo.arrest, label, _joinTable=ArrestRecord)
                count = s.query(func.count(subq.c.arrest))\
                    .all()[0][0]
                # NEED COLOR
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
                color = timeColors[int(hour)]
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

    averages = getAgeData(data)

    data = { 
            'averages': averages
    }

    return jsonify(data)

@app.route('/api/stats/grouping/genders', methods=['GET', 'POST'])
def groupGenderData():
    data = request.get_json()

    maleCounts, femaleCounts = getGenderData(data)
    data = { 
            'maleCounts': maleCounts,
            'femaleCounts': femaleCounts
    }

    return jsonify(data)

@app.route('/api/stats/grouping/times', methods=['GET', 'POST'])
def groupTimeData():
    data = request.get_json()

    dayCounts, nightCounts = getTimesData(data)
    data = {
        'dayCounts': dayCounts,
        'nightCounts': nightCounts
    }

    return jsonify(data)

@app.route('/api/stats/grouping/days', methods=['GET', 'POST'])
def groupDayData():
    data = request.get_json()

    sundayCounts, mondayCounts, tuesdayCounts, wednesdayCounts, \
        thursdayCounts, fridayCounts, saturdayCounts = getDaysData(data)

    data = {
        'sundayCounts': sundayCounts,
        'mondayCounts': mondayCounts,
        'tuesdayCounts': tuesdayCounts,
        'wednesdayCounts': wednesdayCounts,
        'thursdayCounts': thursdayCounts,
        'fridayCounts': fridayCounts,
        'saturdayCounts': saturdayCounts
    }

    return jsonify(data)

    
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
