from flask import Flask, redirect,url_for,render_template,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


user = 'coffeeadmin'
password = 'ilikecoffee'
db = 'CoffeeList'
host = 'localhost'
port = 5432

url = 'sqlite:///sqlite/TestDB.db'
#url = 'postgresql://{}:{}@{}:{}/{}'
url = url.format(user, password, host, port, db)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class history(db.Model):
    historyID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))
    user = db.relationship('user',backref=db.backref('history',lazy='dynamic'))

    itemid = db.Column(db.Integer, db.ForeignKey('item.itemid'))
    item = db.relationship('item',backref=db.backref('items',lazy='dynamic'))

    price = db.Column(db.Float)
    paid = db.Column(db.Boolean)
    date = db.Column(db.DateTime)

    def __init__(self,user,item,price,paid=None,date = None):
        self.user = user
        self.item = item
        self.price = price

        if paid is None:
            paid = False
        self.paid = paid

        if date is None:
            date = datetime.now()
        self.date = date

    def __repr__(self):
        return '<User {} bought {} for {} on the {} >'.format(self.user,self.item,self.price,self.date)

class user(db.Model):
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username

class item(db.Model):
    itemid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True)
    price = db.Column(db.Float)

    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __repr__(self):
        return '<Item %r>' % self.name

@app.route('/')
def hello():
    users = list()

    for instance in user.query:
        users.append({'name': '{}'.format(instance.username),
                      'id': '{}'.format(instance.userid)})

    return render_template('index.html', users=users)

@app.route('/login/<int:userid>',methods = ['GET'])
def login(userid):

    userName = user.query.get(userid).username
    nCoffee =  len(history.query.filter(history.userid == userid ).filter(history.itemid == 1).filter(history.paid == False).all())
    nWater = len(history.query.filter(history.userid == userid ).filter(history.itemid == 2).filter(history.paid == False).all())
    nSnack = len(history.query.filter(history.userid == userid).filter(history.itemid == 3).filter(history.paid == False).all())
    nSoftdrink = len(history.query.filter(history.userid == userid).filter(history.itemid == 4).filter(history.paid == False).all())

    bill = history.query.filter(history.userid == userid).filter(history.paid == False)
    currbill = 0
    for instance in bill:
        currbill += instance.price

    if currbill==None:
        currbill = 0

    return render_template('choices.html',
                           currbill = currbill,
                           chosenuser = userName,
                           userid = userid,
                           nCoffee = nCoffee,
                           nWater = nWater,
                           nSnack = nSnack,
                           nSoftdrink = nSoftdrink)

@app.route('/change/<int:userid>')
def change(userid):

    itemid = request.args.get('itemid')
    curuser = user.query.get(userid)
    curitem = item.query.get(itemid)
    userPurchase = history(curuser,curitem,curitem.price)

    db.session.add(userPurchase)
    db.session.commit()

    return redirect(url_for('login',userid=userid))

if __name__ == "__main__":
    app.run()


