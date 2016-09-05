from sqlalchemy import *
from CoffeeList import makeXLSBill
from datetime import datetime

dbuser = 'coffee'
password = 'ilikecoffee'
db = 'coffeelist'
host = 'localhost'
port = 5432

url = 'postgresql://{}:{}@{}:{}/{}'
url = url.format(dbuser, password, host, port, db)

engine = create_engine(url)
connection = engine.connect()


filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
                                         datetime.now().time().strftime('%H-%M-%S'))
fullpath = ''

makeXLSBill(filename,fullpath)

