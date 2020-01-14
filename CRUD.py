import os, json
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import Column, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import DateTime, Float, Integer, String, Date
from contextlib import contextmanager

from Models import ArrestInfo, ArrestRecord, regenerateTables

user = os.getenv('Postgres_USER')
password = os.getenv('Postgres_PASSWORD')

Base = declarative_base()

dbURL = f'postgresql+psycopg2://{user}:{password}@localhost:5432/wichitaArrests'
engine = create_engine(dbURL)
Session = sessionmaker(bind=engine)

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

def getCSVDates():
    files = os.listdir("CSVs/")
    csvDates = [f.replace('.csv', '') for f in files if f.endswith('.csv')]
    sortedCSVDates = sorted(csvDates, key=lambda x: datetime.strptime(x, '%m-%d-%y'))
    return sortedCSVDates

def getCSVPath(_date):
    return "CSVs/" + _date.replace('/', '-') + ".csv"

def getDataFrameFromCSV(_date):
    path = getCSVPath(_date)
    path = f"C:\\Users\\Jonathan\\Documents\\Visual Studio\\Python Stuff\\Wichita-Arrests\\CSVs\\{_date}.csv"
    df = pd.read_csv(path, sep='|', index_col=False)
    return df

def getCensoredNumber(_number):
    return 'X' * len(_number)

def getCensoredAddress(_address):
    firstWord = _address.partition(' ')[0]
    if firstWord.isnumeric():
        censoredAddress = _address.replace(firstWord, getCensoredNumber(firstWord))
        return censoredAddress
    return _address




def getLastKeyInDB(_session, _column):
    try:
        return _session.query(_column).all().pop()[0]
    except IndexError:
        return 0

def getGroupsFromTags(_tags):
    groups = [next(i['identifier'] for i in filters if i['tag'] == tag) for tag in _tags]
    return groups

def getUsableNumber(_number):
    if type(_number) is int:
        return _number
    elif type(_number) is str and ':' not in _number:
        return None
    else:
        return None

def getTimeOfDay(_time):
    try:
        hour = int(_time.partition(':')[0])
    except ValueError:
        return 'UNKNOWN'
    day = [x for x in range(6, 18)]
    if hour in day:
        timeOfDay = 'DAY'
    else:
        timeOfDay = 'NIGHT'
    return timeOfDay

def getTimeOfYear(_date):
    return datetime.strftime(datetime.strptime(_date, '%m/%d/%Y'), '%B %Y')

def getDayOfTheWeek(_date):
    return datetime.strftime(datetime.strptime(_date, '%m/%d/%Y'), '%A')

if __name__ == "__main__":
    filters = loadJSON('./.Website/static/js/Filters.json')
    regenerateTables()
    dfCoordinates = pd.read_csv('addressCoords.csv', sep=';', index_col=False)

    with sessionManager() as s:

        for date in getCSVDates():
            print(f"Inserting from...CSVs/{date}.csv")
            df = getDataFrameFromCSV(date)
            lastKey = getLastKeyInDB(s, ArrestRecord.recordID)
            arrestInfoKey = getLastKeyInDB(s, ArrestInfo.arrestID)
            #print(lastKey)
            #print(arrestInfoKey)

            for index, row in df.iterrows():
                matchingSeries = dfCoordinates.loc[dfCoordinates['Address'] == row['Address']]
                latitude = matchingSeries['Latitude'].values[0]
                longitude = matchingSeries['Longitude'].values[0]
                tags = row['Tags'].split(';')
                groups = getGroupsFromTags(tags)
                identifyingGroup = max(groups, key=groups.count)
                age = getUsableNumber(row['Age'])
                birthdate = getUsableNumber(row['Birthdate'])
                time = getUsableNumber(row['Time'])

                currentKey = lastKey + index + 1
                #print(currentKey)
                s.add(
                    ArrestRecord(
                        recordID = currentKey,
                        name = row['Name'],
                        date = row['Date'],
                        time = time,
                        birthdate = birthdate,
                        age = age,
                        race = row['Race'],
                        sex = row['Sex'],
                        address = row['Address'],
                        censoredAddress = getCensoredAddress(row['Address']),
                        latitude = latitude,
                        longitude = longitude,
                        incidents = row['Incidents'],
                        identifyingGroup = identifyingGroup
                    )
                )
                
                arrests = row['Arrests'].split(';')
                warrants = row['Warrants']
                timeOfDay = getTimeOfDay(row['Time'])
                timeOfYear = getTimeOfYear(row['Date'])
                dayOfTheWeek = getDayOfTheWeek(row['Date'])

                


                recordsToAdd = [ArrestInfo(
                                    arrestRecordFKey=currentKey,
                                    arrest=arrest,
                                    tag=tags[i],
                                    group=groups[i],
                                    warrant=None,
                                    timeOfDay=timeOfDay,
                                    timeOfYear=timeOfYear,
                                    dayOfTheWeek=dayOfTheWeek)
                                for i, arrest in enumerate(arrests) 
                                if arrest != "No arrests listed."]

                s.add_all(recordsToAdd)


                if type(warrants) is str:
                    recordsToAdd = [ArrestInfo(
                        arrestRecordFKey=currentKey,
                        arrest=None,
                        tag='Warrants',
                        group='Warrants',
                        warrant=warrant,
                        timeOfDay=timeOfDay,
                        timeOfYear=timeOfYear,
                        dayOfTheWeek=dayOfTheWeek) 
                    for i, warrant in enumerate(warrants.split(';'))]
                s.add_all(recordsToAdd)