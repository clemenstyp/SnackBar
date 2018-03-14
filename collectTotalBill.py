# coding: utf-8
from sqlalchemy import *
from CoffeeList import makeXLSBill,user,restBill
from datetime import datetime
from sendEmail import Bimail
import os

user = 'coffee'
password = 'ilikecoffee'
db = 'coffeelist'
host = 'localhost'
port = 5432
coffeeMaster = "Clemens"

url = 'sqlite:///CoffeeDB.db'
# url = 'postgresql://{}:{}@{}:{}/{}'
url = url.format(user, password, host, port, db)

engine = create_engine(url)
connection = engine.connect()

filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
                                         datetime.now().time().strftime('%H-%M-%S'))
fullpath = 'static'

makeXLSBill(filename,fullpath)


print('Start sending emails.')
print(datetime.now().time().strftime('%H-%M-%S'))
# subject and recipients
for instance in user.query:
    if instance.email:

        currbill = '{0:.2f}'.format(restBill(instance.userid))
        #print(instance.firstName)
        #print(currbill)
        mymail = Bimail('Coffebill for the ' + datetime.now().strftime('%Y/%m/%d'), ['{}'.format(instance.email)])
        mymail.sendername = 'kaffeekiosk-noreply@fit.fraunhofer.de'
        mymail.sender = 'kaffeekiosk-noreply@fit.fraunhofer.de'
        mymail.servername = 'smtp.fit.fraunhofer.de:587'
        # start html body. Here we add a greeting.
        mymail.htmladd('Good morning {} {}. <br> Your Bill is {} € <br><br>'.format(instance.firstName,instance.lastName,currbill))
        # Further things added to body are separated by a paragraph, so you do not need to worry about newlines for new sentences
        # here we add a line of text and an html table previously stored in the variable
        # add image chart title
        # attach another file
        mymail.htmladd('Please pay your remaining bill to ' + coffeeMaster +' as soon as possible.')
        #mymail.addattach([os.path.join(fullpath, filename)])
        # send!
        print(mymail.htmlbody)
        #mymail.send()
    else:
        continue
