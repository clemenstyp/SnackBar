# coding: utf-8
from datetime import datetime

from sqlalchemy import *

from SnackBar import make_xls_bill, User, rest_bill
from sendEmail import Bimail

userName = 'coffee'
password = 'ilikecoffee'
db = 'coffeelist'
host = 'localhost'
port = 5432
coffeeMaster = "Clemens"

url = 'sqlite:///CoffeeDB.db'
# url = 'postgresql://{}:{}@{}:{}/{}'
url = url.format(userName, password, host, port, db)

engine = create_engine(url)
connection = engine.connect()

filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
                                         datetime.now().time().strftime('%H-%M-%S'))
fullpath = 'static'

make_xls_bill(filename, fullpath)

print('Start sending emails.')
print(datetime.now().time().strftime('%H-%M-%S'))
# subject and recipients
for instance in User.query:
    if instance.email:

        currbill = '{0:.2f}'.format(rest_bill(instance.userid))
        # print(instance.firstName)
        # print(currbill)
        mymail = Bimail('Coffebill for the ' + datetime.now().strftime('%Y/%m/%d'), ['{}'.format(instance.email)])
        mymail.sendername = 'kaffeekiosk-noreply@fit.fraunhofer.de'
        mymail.sender = 'kaffeekiosk-noreply@fit.fraunhofer.de'
        mymail.servername = 'smtp.fit.fraunhofer.de:587'
        # start html body. Here we add a greeting.
        mymail.htmladd(
            'Good morning {} {}. <br> Your Bill is {} € <br><br>'.format(instance.firstName, instance.lastName,
                                                                         currbill))
        # Further things added to body are separated by a paragraph, so you do not need to worry about newlines
        # for new sentences here we add a line of text and an html table previously stored in the variable
        # add image chart title
        # attach another file
        mymail.htmladd('Please pay your remaining bill to ' + coffeeMaster + ' as soon as possible.')
        # mymail.addattach([os.path.join(fullpath, filename)])
        # send!
        print(mymail.htmlbody)
        # mymail.send()
    else:
        continue
