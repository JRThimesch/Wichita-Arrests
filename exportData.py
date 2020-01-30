import os, json
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import Column, create_engine, ForeignKey, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import DateTime, Float, Integer, String, Date
from contextlib import contextmanager

from Models import ArrestInfo, ArrestRecord

user = os.getenv('Postgres_USER')
password = os.getenv('Postgres_PASSWORD')

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

if __name__ == "__main__":
    with sessionManager() as s:
        query = s.query(ArrestRecord.address, ArrestRecord.latitude, ArrestRecord.longitude).distinct().all()
        data = [list(item) for item in query]
    df = pd.DataFrame(data=data, columns=['Address', 'Latitude', 'Longitude'])
    df.to_csv(index=False, sep=';', path_or_buf='addressCoords.csv')