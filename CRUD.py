import os, json
import pandas as pd
import numpy as np
from datetime import datetime, date
from contextlib import contextmanager
from sqlalchemy import Column, create_engine, ForeignKey, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import DateTime, Float, Integer, String, Date
from geopy.geocoders import GoogleV3

from Models import ArrestInfo, ArrestRecord, regenerateTables

user = os.getenv('Postgres_USER')
password = os.getenv('Postgres_PASSWORD')
API_KEY = os.getenv('GOOGLEAPI_KEY')

Base = declarative_base()

dbURL = f'postgresql+psycopg2://{user}:{password}@localhost:5432/wichitaArrests'
engine = create_engine(dbURL)
Session = sessionmaker(bind=engine)

googleAPI = GoogleV3(api_key=API_KEY)

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
        lastKey = _session.query(_column).order_by(desc(_column)).first()[0]
        return lastKey
    except TypeError:
        return 0

def getGroupsFromTags(_tags):
    groups = [next(i['identifier'] for i in filters if i['tag'] == tag) for tag in _tags]
    return groups

def getUsableNumber(_number):
    try:
        return int(_number)
    except:
        return None

def getUsableDate(_date):
    if '/' in _date:
        return _date
    else:
        return None

def getUsableTime(_time):
    if ':' in _time:
        return _time
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

def getListQuery(_query):
    return list(zip(*_query))[0]

def isAddressInDB(_session, _address):
    query = _session.query(ArrestRecord.address).distinct().all()
    listQuery = [i for i, in query]
    return _address in listQuery

def getCoordinatesFromDB(_session, _address):
    print(f"Matching {_address} to DB")
    return _session.query(ArrestRecord.latitude, ArrestRecord.longitude)\
        .filter(ArrestRecord.address == _address).first()

def getQueriedCoordinates(_address):
    try:
        _, coordinates = googleAPI.geocode(query=_address)
        return coordinates
    except Exception as e:
        print(e)
        print('Error with address:', _address)
        print('Retrying on', _address)
        return getQueriedCoordinates(_address)

def getCoordinates(_session, _address):
    if _address == 'No address listed.':
        return (37.6872, -97.3301)
    if isAddressInDB(_session, _address):
        return getCoordinatesFromDB(_session, _address)
    else:
        extendedAddress = _address + " Wichita, Kansas, USA"
        return getQueriedCoordinates(extendedAddress)

def getExistingDates(_session):
    query = _session.query(ArrestRecord.date)\
        .distinct().all()
    dates = [date.strftime(i, '%m-%d-%y') for i, in query]
    return dates

def getMissingDates(_session):
    existingDates = getExistingDates(_session)
    allCSVDates = getCSVDates()
    return [date for date in allCSVDates if date not in existingDates]

def writeFromCSVs(_session, rewrite=False):
    if rewrite:
        dfCoordinates = pd.read_csv('addressCoords.csv', sep=';', index_col=False)
        dates = getCSVDates()
    else:
        dates = getMissingDates(_session)

    for date in dates:
        print(f"Inserting from...CSVs/{date}.csv")
        df = getDataFrameFromCSV(date)
        lastKey = getLastKeyInDB(_session, ArrestRecord.recordID)

        for index, row in df.iterrows():
            if rewrite:
                try:
                    matchingSeries = dfCoordinates.loc[dfCoordinates['Address'] == row['Address']]
                    latitude = matchingSeries['Latitude'].values[0]
                    longitude = matchingSeries['Longitude'].values[0]
                except:
                    latitude, longitude = getCoordinates(_session, row['Address'])
            else:
                latitude, longitude = getCoordinates(_session, row['Address'])
            try:
                tags = row['Tags'].split(';')
                groups = getGroupsFromTags(tags)
                identifyingGroup = max(groups, key=groups.count)
            except AttributeError:
                tags = None
                groups = None
                identifyingGroup = None
            age = getUsableNumber(row['Age'])
            birthdate = getUsableDate(row['Birthdate'])
            time = getUsableTime(row['Time'])
            timeOfDay = getTimeOfDay(row['Time'])
            timeOfYear = getTimeOfYear(row['Date'])
            dayOfTheWeek = getDayOfTheWeek(row['Date'])
            currentKey = lastKey + index + 1

            _session.add(
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
                    identifyingGroup = identifyingGroup,
                    timeOfDay=timeOfDay,
                    timeOfYear=timeOfYear,
                    dayOfTheWeek=dayOfTheWeek
                )
            )
            
            arrests = row['Arrests'].split(';')
            warrants = row['Warrants']

            recordsToAdd = []
            for i, arrest in enumerate(arrests):
                if arrest != 'No arrests listed.':
                    recordsToAdd.append(ArrestInfo(
                                arrestRecordFKey=currentKey,
                                arrest=arrest,
                                tag=tags[i],
                                group=groups[i],
                                warrant=None))
                elif type(warrants) is float:
                    print(arrests)
                else:
                    recordsToAdd.append(ArrestInfo(
                                arrestRecordFKey=currentKey,
                                arrest=None,
                                tag=None,
                                group=None,
                                warrant=None))

            _session.add_all(recordsToAdd)

            if type(warrants) is str:
                recordsToAdd = [ArrestInfo(
                    arrestRecordFKey=currentKey,
                    arrest=None,
                    tag='Warrants',
                    group='Warrants',
                    warrant=warrant) 
                for i, warrant in enumerate(warrants.split(';'))]

            _session.add_all(recordsToAdd)

def prompt():
    response = input("1. Insert Data\n2. View Data\n3. Update Data\n4. Delete Data\n5. Regen Tables\n6. Regen and Rewrite Tables\n7. Debug (CHANGES AS NEEDED)\n")
    rangeOfResponses = [x for x in range(1, 8)]
    try:
        if int(response) not in rangeOfResponses:
            print("Exiting...")
            raise SystemExit
    except:
        raise SystemExit
    return int(response)

def selectAction():
    response = prompt()

    with sessionManager() as s:
        if response == 1:
            writeFromCSVs(s, rewrite=False)
        elif response == 5:
            regenerateTables()
        elif response == 6:
            regenerateTables()
            writeFromCSVs(s, rewrite=True)
        elif response == 7:
            writeFromCSVs(s, rewrite=True)

if __name__ == "__main__":
    filters = loadJSON('./.Website/static/js/Filters.json')
    selectAction()