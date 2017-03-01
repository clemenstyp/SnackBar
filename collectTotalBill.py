from sqlalchemy import *
from CoffeeList import makeXLSBill,user,getcurrbill
from datetime import datetime
from sendEmail import Bimail
import os

dbuser = 'coffee'
password = 'ilikecoffee'
db = 'coffeelist'
host = 'localhost'
port = 5432

url = 'sqlite:///TestDB.db'
#url = 'postgresql://{}:{}@{}:{}/{}'
url = url.format(user, password, host, port, db)

engine = create_engine(url)
connection = engine.connect()

filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
                                         datetime.now().time().strftime('%H-%M-%S'))
fullpath = 'static'

makeXLSBill(filename,fullpath)


import credentials
print('Start sending emails.')
print(datetime.now().time().strftime('%H-%M-%S'))
# subject and recipients
for instance in user.query:
    if instance.email:
        currbill = '{0:.2f}'.format(getcurrbill(instance.userid))
        type(currbill)
        mymail = Bimail('CoffeList for the ' + datetime.now().strftime('%Y/%m/%d'), ['{}'.format(instance.email)])
        mymail.sendername = 'coffeebill@james.uni-marburg.de'
        mymail.sender = credentials.username
        mymail.senderpass = credentials.password
        mymail.servername = 'smtp.staff.uni-marburg.de:587'
        # start html body. Here we add a greeting.
        mymail.htmladd('Good morning {} {}. <br> Your Bill is {} € <br> You can find detailed version of the current coffeelist bill attached to this email.<br>'.format(instance.firstName,instance.lastName,currbill))
        # Further things added to body are separated by a paragraph, so you do not need to worry about newlines for new sentences
        # here we add a line of text and an html table previously stored in the variable
        # add image chart title
        # attach another file
        mymail.htmladd('Please pay your remaining bill as soon as possible.')
        mymail.addattach([os.path.join(fullpath, filename)])
        # send!
        print(mymail.htmlbody)
        #mymail.send()
    else:
        continue

print('Finished sending emails.')
print(datetime.now().time().strftime('%H-%M-%S'))