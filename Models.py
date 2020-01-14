import os
from sqlalchemy import Column, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import DateTime, Float, Integer, String, Date

user = os.getenv('Postgres_USER')
password = os.getenv('Postgres_PASSWORD')

Base = declarative_base()

dbURL = f'postgresql+psycopg2://{user}:{password}@localhost:5432/wichitaArrests'
engine = create_engine(dbURL)

class ArrestRecord(Base):
    __tablename__ = 'ArrestRecords'

    recordID = Column(Integer, primary_key=True)
    name = Column(String(length=128))
    date = Column(Date())
    birthdate = Column(Date())
    age = Column(Integer())
    time = Column(String(length=5))
    race = Column(String(length=32))
    sex = Column(String(length=6))
    address = Column(String(length=128))
    censoredAddress = Column(String(length=128))
    latitude = Column(Float())
    longitude = Column(Float())
    incidents = Column(String(length=1024))
    identifyingGroup = Column(String(length=48))

    children = relationship("ArrestInfo")

class ArrestInfo(Base):
    __tablename__ = 'ArrestInfo'

    arrestID = Column(Integer, primary_key=True)
    arrestRecordFKey = Column(Integer(), ForeignKey('ArrestRecords.recordID'))
    arrest = Column(String(length=128))
    warrant = Column(String(length=10))
    tag = Column(String(length=48))
    group = Column(String(length=48))
    timeOfDay = Column(String(length=16))
    timeOfYear = Column(String(length=32))
    dayOfTheWeek = Column(String(length=16))

def createTables():
    Base.metadata.create_all(engine)

def deleteTables():
    warning = 'WARNING: ABOUT TO DELETE ALL TABLES.\n\tARE YOU CERTAIN? (Y/N)\t'
    response = input(warning).lower()
    if response == 'y':
        Base.metadata.drop_all(engine)

def regenerateTables():
    deleteTables()
    createTables()