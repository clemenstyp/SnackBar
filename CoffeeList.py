from flask import Flask, redirect,url_for
from flask import render_template
from flask import request
from ldap3 import Server, Connection, ALL, NTLM
import sqlite3
from sqlalchemy import Column, ForeignKey, Integer, String, Table, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, MetaData, select

Base = declarative_base()

user = 'coffeeadmin'
password = 'ilikecoffee'
db = 'CoffeeList'
host = 'localhost'
port = 5432

priceCoffe = 0.4
priceSnacks= 0.6
priceWater = 0.9

url = 'sqlite:///sqlite/TestDB.db'
#url = 'postgresql://{}:{}@{}:{}/{}'
url = url.format(user, password, host, port, db)

class CoffeeList(Base):
     __tablename__ = 'coffeelist'

     id       = Column(Integer, primary_key=True)
     name     = Column(String)
     ncoffee  = Column(Integer)
     nsnacks  = Column(Integer)
     nwater   = Column(Integer)
     currbill = Column(Integer)

     def __repr__(self):
        return "<User(name='%s')>" % (
                             self.name)
def updateBill(nCoffeeUser, nWaterUser,nSnacksUser):
    currBill = nCoffeeUser*priceCoffe+nWaterUser*priceWater+nSnacksUser*priceSnacks
    return currBill

def connect_db(url):
    engine = create_engine(url, convert_unicode='utf8')
    metadata = MetaData(bind=engine, reflect=True)

    Session = sessionmaker(bind=engine)
    myfirstSession = Session()
    return myfirstSession

app = Flask(__name__)
@app.route('/test', methods=['GET'])
def test():
    print(request.args.get('a'))
    print(request.args.get('b'))


@app.route('/')
def hello():
    myfirstSession = connect_db(url)
    users = list()

    for instance in myfirstSession.query(CoffeeList):
        users.append({'name': '{}'.format(instance.name),
                      'id': '{}'.format(instance.id)})

    return render_template('index.html', users=users)

@app.route('/login/<int:userid>',methods = ['GET'])
def login(userid):

    myfirstSession = connect_db(url)

    for instance in myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid):
        userName = instance.name
        nCoffeeUser = instance.ncoffee
        nSnacksUser = instance.nsnacks
        nWaterUser = instance.nwater
        currbill = instance.currbill

    return render_template('choices.html',currbill = currbill,
                                          chosenuser=userName,
                                          nCoffee=nCoffeeUser,
                                          userid=userid,
                                          nWater=nWaterUser,
                                          nSnacks=nSnacksUser)

@app.route('/change/<int:userid>')
def change(userid):

    myfirstSession = connect_db(url)

    action =  request.args.get('act')
    item = request.args.get('item')


    for instance in myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid):
        userName = instance.name
        nCoffeeUser = instance.ncoffee
        nWaterUser = instance.nwater
        nSnacksUser = instance.nsnacks

    if item =='coffee':
        if action=='add':
            myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.ncoffee: CoffeeList.ncoffee+1})
            currbill = updateBill(nCoffeeUser+1,nWaterUser,nSnacksUser)
            myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.currbill: currbill})
            myfirstSession.commit()

        elif action=='del':
            if nCoffeeUser-1 >= 0:
                myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.ncoffee: CoffeeList.ncoffee-1})
                currbill = updateBill(nCoffeeUser-1, nWaterUser, nSnacksUser)
                myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.currbill: currbill})
                myfirstSession.commit()

    if item == 'water':
        if action == 'add':
            myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.nwater: CoffeeList.nwater + 1})
            currbill = updateBill(nCoffeeUser,nWaterUser+1,nSnacksUser)
            myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.currbill: currbill})
            myfirstSession.commit()
        elif action == 'del':
            if nWaterUser-1 >= 0:
                myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.nwater: CoffeeList.nwater - 1})
                currbill = updateBill(nCoffeeUser, nWaterUser-1, nSnacksUser)
                myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.currbill: currbill})
                myfirstSession.commit()

    if item == 'snacks':
        if action == 'add':
            myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.nsnacks: CoffeeList.nsnacks + 1})
            currbill = updateBill(nCoffeeUser, nWaterUser, nSnacksUser+1)
            myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.currbill: currbill})
            myfirstSession.commit()
        elif action == 'del':
            if nSnacksUser-1 >= 0:
                myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.nsnacks: CoffeeList.nsnacks - 1})
                currbill = updateBill(nCoffeeUser, nWaterUser, nSnacksUser-1)
                myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid).update({CoffeeList.currbill: currbill})
                myfirstSession.commit()



    return redirect(url_for('login',userid=userid))

if __name__ == "__main__":
    app.run()


