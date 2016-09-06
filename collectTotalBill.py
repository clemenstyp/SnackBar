from sqlalchemy import *
from CoffeeList import makeXLSBill
from datetime import datetime
from sendEmail import Bimail
import os

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
fullpath = 'static'

makeXLSBill(filename,fullpath)

import credentials
# subject and recipients
mymail = Bimail('CoffeList for the ' + datetime.now().strftime('%Y/%m/%d'), ['recipient@provider.com'])
mymail.sendername = 'Nameofthesender@provider.com'
mymail.sender = credentials.username
mymail.senderpass = credentials.password
mymail.servername = 'name.of.the.smtp.server:587'

# start html body. Here we add a greeting.
mymail.htmladd('Godd Morning<br>You can find detailed version of the current coffeelist bill in the attachement.<br>')
# Further things added to body are separated by a paragraph, so you do not need to worry about newlines for new sentences
# here we add a line of text and an html table previously stored in the variable
# add image chart title
# attach another file
mymail.addattach([os.path.join(fullpath, filename)])
# send!
mymail.send()