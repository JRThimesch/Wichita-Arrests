import os, json
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import Column, create_engine, ForeignKey, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import DateTime, Float, Integer, String, Date
from contextlib import contextmanager

user = os.getenv('Postgres_USER')
password = os.getenv('Postgres_PASSWORD')

dbURL = f'postgresql+psycopg2://{user}:{password}@localhost:5432/wichita-arrests'
engine = create_engine(dbURL)
metadata = MetaData()
wichitaArrests = Table('wichita-arrests', metadata, autoload=True, autoload_with=engine)
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

if __name__ == "__main__":
    with sessionManager() as s:
        test = s.query(wichitaArrests.c.address, wichitaArrests.c.lat, wichitaArrests.c.lng).distinct().all()
        data = [list(item) for item in test]
    df = pd.DataFrame(data=data, columns=['Address', 'Latitude', 'Longitude'])
    df.to_csv(index=False, sep=';', path_or_buf='addressCoords.csv')