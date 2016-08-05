from flask import Flask
from flask import render_template
from flask import request
from ldap3 import Server, Connection, ALL, NTLM
import sqlite3
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, MetaData, select

Base = declarative_base()

user = 'coffeeadmin'
password = 'ilikecoffee'
db = 'CoffeeList'
host = 'localhost'
port = 5432

url = 'postgresql://{}:{}@{}:{}/{}'
url = url.format(user, password, host, port, db)

class CoffeeList(Base):
     __tablename__ = 'coffeelist'

     id = Column(Integer, primary_key=True)
     name = Column(String)
     ncoffee = Column(Integer)

     def __repr__(self):
        return "<User(name='%s')>" % (
                             self.name)

engine = create_engine(url, client_encoding='utf8')
metadata = MetaData(bind=engine, reflect=True)

Session = sessionmaker(bind=engine)
myfirstSession = Session()

for instance in myfirstSession.query(CoffeeList).order_by(CoffeeList.ncoffee):
    print(instance.name, instance.ncoffee)


exit(0)

#postgresql+pygresql://user:password@host:port/dbname[?key=value&key=value]

# conn = sqlite3.connect('sqlite/CoffeeList.db')
# c = conn.cursor()
#
# c.execute("SELECT name,nCoffee from coffeelist WHERE name='Lennart Duschek'")
# for record in c.fetchall():
#     userName=record[0]
#     nCoffee=record[1]
#
# print(userName)
# print(nCoffee)
#
# #c.execute("UPDATE coffeelist SET nCoffee={} WHERE name=name".format(nCoffeeUser))
# #conn.commit()
# conn.close()
#
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def hello():

    # server = Server('Server', get_info=ALL)
    # conn = Connection(server, user='username', password='password', auto_bind=True)
    # # print(server.info)
    # # print(server.schema)
    # conn.search(search_base='dc=Physik,dc=Uni-Marburg,dc=DE',
    #             search_filter='(|(memberOf=cn=uni-fb13_wzmw,ou=groups,ou=uni-fb13,dc=physik,dc=uni-marburg,dc=de)(gidNumber=1000100))',
    #             attributes=['cn', 'givenName', 'sn', 'userPrincipalName'])
    # # print(conn.entries)
    #
    # users = list()
    # for item in conn.entries:
    #     if 'givenName' in item.entry_get_attributes_dict().keys():
    #         users.append({'name': '{} {}'.format(item.givenName, item.sn)})
    # conn.closed
    conn = sqlite3.connect('sqlite/CoffeeList.db')
    c = conn.cursor()

    c.execute("SELECT * from coffeelist")
    users = list()
    for rows in c.fetchall():
        users.append({'name': '{}'.format(rows[1]),
                     'id': '{}'.format(rows[0])})

    conn.close()

    return render_template('index.html', users=users)

@app.route('/login/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        userid = request.form['UserButton']
        conn = sqlite3.connect('sqlite/CoffeeList.db')
        c = conn.cursor()
        c.execute("SELECT name,nCoffee from coffeelist WHERE id={}".format(userid))
        for record in c.fetchall():
            userName = record[0]
            nCoffeeUser = int(record[1])

    return render_template('choices.html',chosenuser=userName,nCoffee=nCoffeeUser)
