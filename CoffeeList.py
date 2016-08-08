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

url = 'sqlite:///sqlite/CoffeeList.db'
url = url.format(user, password, host, port, db)

class CoffeeList(Base):
     __tablename__ = 'coffeelist'

     id = Column(Integer, primary_key=True)
     name = Column(String)
     ncoffee = Column(Integer)

     def __repr__(self):
        return "<User(name='%s')>" % (
                             self.name)

def connect_db(url):
    engine = create_engine(url, convert_unicode='utf8')
    metadata = MetaData(bind=engine, reflect=True)

    Session = sessionmaker(bind=engine)
    myfirstSession = Session()
    return myfirstSession

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def hello():
    myfirstSession = connect_db(url)

    users = list()

    for instance in myfirstSession.query(CoffeeList):
        users.append({'name': '{}'.format(instance.name),
                      'id': '{}'.format(instance.id)})

    return render_template('index.html', users=users)

@app.route('/login/<int:userid>')
def login(userid):

    myfirstSession = connect_db(url)

    for instance in myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid):
        userName = instance.name
        nCoffeeUser = instance.ncoffee

    return render_template('choices.html',chosenuser=userName,nCoffee=nCoffeeUser, userid=userid)

@app.route('/change/<int:userid>')
def change(userid):
    addcoffee = "add"

    myfirstSession = connect_db(url)

    for instance in myfirstSession.query(CoffeeList).filter(CoffeeList.id == userid):
        userName = instance.name
        nCoffeeUser = instance.ncoffee

    if addcoffee=='add':
        myfirstSession.query(CoffeeList).update({CoffeeList.ncoffee: CoffeeList.ncoffee+1})
        myfirstSession.commit()


        return redirect(url_for('login',userid=userid))

if __name__ == "__main__":
    app.run()

