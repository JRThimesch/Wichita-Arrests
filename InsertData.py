import glob
import os
import csv
import sqlalchemy as SQLAlchemy

csv.register_dialect('dialect',
    delimiter = '|',
    quoting = csv.QUOTE_NONE,
    skipinitialspace = True)

db = SQLAlchemy.create_engine(key)
conn = db.connect()
metadata = SQLAlchemy.MetaData()
arrestDB = SQLAlchemy.Table(table, metadata, autoload=True, autoload_with=db)

query = SQLAlchemy.select([arrestDB])
result = conn.execute(query)

dates = list(set([row['date'] for row in result]))
dates.sort()
for i, e in enumerate(dates):
    dates[i] = e.replace('/', '-')

path = 'CSVs/*'
files = glob.glob(path)
sortedFiles = sorted(files, key = os.path.getmtime)

for file in sortedFiles:
    if os.path.splitext(os.path.basename(file))[0] not in dates:
        with open(file, 'r') as f:
            print('Inserting from', file, '...')
            reader = csv.reader(f, dialect = 'dialect')
            rows = list(reader)
            for e in rows:
                if e:
                    statement = arrestDB.insert().values(name = e[0], 
                    date = e[1], dob = e[2], age = e[3], time = e[4], 
                    race = e[5], address = e[6], arrests = e[7], 
                    incidents = e[8], warrants = e[9], censoredAddress = e[10], 
                    lat = e[11], long = e[12])
                    
                    conn.execute(statement)
