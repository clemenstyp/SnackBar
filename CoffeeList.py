import os, tablib, random
from flask import Flask, redirect,url_for,render_template,request, send_from_directory,current_app
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin,expose,helpers,AdminIndexView, BaseView
from flask_admin.contrib.sqla import ModelView
import flask_login as loginflask
from wtforms import form, fields, validators
from datetime import datetime
from jinja2 import Markup

user = 'coffee'
password = 'ilikecoffee'
db = 'coffee'
host = 'localhost'
port = 5432

#url = 'sqlite:///TestDB.db'
url = 'postgresql://{}:{}@{}:{}/{}'
url = url.format(user, password, host, port, db)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = '123456790'
app.config['STATIC_FOLDER'] = 'static'

db = SQLAlchemy(app)

@app.template_filter("itemstrikes")
def itemstrikes(value):
    counter = 0
    tag_opened = False
    out = ""
    if value > 4:
        out = "<s>"
        tag_opened = True
    for f in range(value):
        counter += 1
        if counter % 5 == 0:
            out += "</s> "
            if value - counter > 4:
                out += "<s>"
        else:
            out += "|"
    if tag_opened:
        out += "</s>"
    out += " (%d)" % value
    return Markup(out)

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
        return 'User {} bought {} for {} on the {}'.format(self.user,self.item,self.price,self.date)

colors = ('red','orange','yellow','olive','green','teal','blue','violet','purple',
          'pink','brown','grey','black')

class inpayment(db.Model):

    paymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))
    user = db.relationship('user', backref=db.backref('inpayment', lazy='dynamic'))

    amount = db.Column(db.Float)
    rest = db.Column(db.Float)
    date = db.Column(db.DateTime)

    def __init__(self, user=None, amount=None, rest = amount, date=None):
        self.userid = user

        if amount is None:
            amount = 0
        self.amount = amount

        self.rest = rest

        if date is None:
            date = datetime.now()
        self.date = date

    def __repr__(self):
        return 'User {} paid {} on the {}'.format(self.userid, self.amount, self.date)


class user(db.Model):
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    btncolor = db.Column(db.String(80))


    def __init__(self, username='', email='', btncolor=None):
        self.username = username
        self.email = email
        if btncolor is None:
            btncolor = random.choice(colors)
        self.btncolor = btncolor


    def __repr__(self):
        return self.username

class item(db.Model):
    itemid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True)
    price = db.Column(db.Float)

    def __init__(self, name='', price=0):
        self.name = name
        self.price = price

    def __repr__(self):
        return self.name


class coffeeadmin(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(64))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class LoginForm(form.Form):
    login = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        # we're comparing the plaintext pw with the the hash from the db
        if user.password != self.password.data:
        # to compare plain text passwords use
        # if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(coffeeadmin).filter_by(name=self.login.data).first()

class RegistrationForm(form.Form):
    login = fields.StringField(validators=[validators.required()])
    email = fields.StringField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if db.session.query(coffeeadmin).filter_by(name=self.login.data).count() > 0:
            raise validators.ValidationError('Duplicate username')

def init_login():
    login_manager = loginflask.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(coffeeadmin).get(user_id)

def getcurrbill(userid):
    bill = history.query.filter(history.userid == userid).filter(history.paid == False)
    currbill = 0

    for entry in bill:
        currbill += entry.price
    return currbill

def getunpaid(userid,itemid):

    nUnpaid = len(history.query.filter(history.userid == userid).
        filter(history.itemid == itemid).
        filter(history.paid == False).all())

    return nUnpaid


def accountPayment(userid):

    if len(history.query.filter(history.userid == userid).filter(history.paid == False).all()) != 0:
        if len(inpayment.query.filter(inpayment.userid == userid).filter(inpayment.rest != 0).all()) != 0:

            purchase = history.query.filter(history.userid == userid).filter(history.paid == False)
            inpay = inpayment.query.filter(inpayment.userid == userid).filter(inpayment.rest != 0).all()
            transfer = 0

            for instance in purchase:
                print(instance)
                for entry in inpay:
                    print(entry)
                    if entry.rest + transfer - instance.price < 0:
                        print('Geld aus erstem Eintrag reicht nicht')
                        if len(inpayment.query.filter(inpayment.userid == userid).filter(inpayment.rest != 0).all()) > 1:
                            print('Transferiere Geld aus erstem Eintrag')
                            transfer = entry.rest
                            print(transfer)
                            entry.rest = 0
                            entry.date = datetime.now()

                        continue

                    else:
                        print('Geld aus eintrag ist genug')
                        print(entry.rest + transfer)
                        entry.rest = entry.rest + transfer - instance.price
                        instance.paid = True
                        entry.date = datetime.now()
                        transfer = 0
                        print('Neuer Betrag ist')
                        print(entry.rest)

        else:
            print('Unpaid Bills but no InPay')

    else:
        print('Nothing to pay')

    db.session.commit()

    return

class AnalyticsView(BaseView):

    @expose('/')
    def index(self):

        users = list()
        for instance in user.query:
            bill = history.query.filter(history.userid == instance.userid).filter(history.paid == False)
            currbill = 0

            for entry in bill:
                currbill += entry.price

            users.append({'name': '{}'.format(instance.username),
                          'userid':'{}'.format(instance.userid),
                          'bill': currbill})

        return self.render('admin/test.html',users = users)

    @expose('/paid/', methods=['GET'])
    def paid(self):

        userid = request.args.get('userid')
        print(userid)
        purchase = history.query.filter(history.userid == userid).filter(history.paid == False)

        for entry in purchase:
            entry.paid = True

        db.session.commit()
        return redirect(url_for('.index'))

    @expose('/export/')
    def export(self):
        filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
                                                 datetime.now().time().strftime('%H-%M-%S'))

        fullpath = os.path.join(current_app.root_path, app.config['STATIC_FOLDER'])
        header = list()
        header.append('name')
        for entry in item.query:
            header.append('{}'.format(entry.name))
        header.append('bill')

        excelData = tablib.Dataset()
        excelData.headers = header

        for instance in user.query:
            firstline = list()
            firstline.append('{}'.format(instance.username))

            for record in item.query:
                firstline.append('{}'.format(getunpaid(instance.userid, record.itemid)))

            firstline.append('{0:.2f}'.format(getcurrbill(instance.userid)))
            excelData.append(firstline)

        with open(os.path.join(fullpath,filename), 'wb') as f:
            f.write(excelData.xls)

        return send_from_directory(directory=fullpath, filename=filename, as_attachment=True)

    def is_accessible(self):
        return loginflask.current_user.is_authenticated


class MyPaymentModelView(ModelView):
    can_create = True
    can_export = True
    export_types = ['csv']

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

class MyHistoryModelView(ModelView):
    can_create = False
    can_export = True
    export_types = ['csv']
    column_descriptions = dict(
        paid='Indicates if the purchase is already paid.'
    )
    column_labels = dict(user='Name')

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

class MyUserModelView(ModelView):
    can_export = True
    export_types = ['csv', 'xls']
    form_excluded_columns = ('history')
    column_descriptions = dict(
        username='Name of the corresponding person'
    )
    column_labels = dict(username='Name',btncolor='Button Color')
    #form_choices = {'username' : ['Lennart','Lukas'],
    #               'email' : [],
    #                'btncolor' : []}

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

class MyItemModelView(ModelView):
    can_export = True
    export_types =['csv','xls']
    form_excluded_columns = ('items')

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

class MyAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        if not loginflask.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()
        #return redirect(url_for('bill.index'))

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            loginflask.login_user(user)

        if loginflask.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
#        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        loginflask.logout_user()
        return redirect(url_for('.index'))

init_login()
admin = Admin(app, name = 'CoffeeList Admin Page',index_view=MyAdminIndexView(), base_template='my_master.html')
admin.add_view(AnalyticsView(name='Bill', endpoint='bill'))
admin.add_view(MyUserModelView(inpayment, db.session, 'InPayment'))
admin.add_view(MyUserModelView(user, db.session, 'User'))
admin.add_view(MyItemModelView(item, db.session,'Items'))
admin.add_view(MyHistoryModelView(history, db.session,'History'))


@app.route('/')
def hello():
    initusers = list()

    for instance in user.query:
        initusers.append({'name': '{}'.format(instance.username),
                      'id': '{}'.format(instance.userid),
                      'bill': getcurrbill(instance.userid),
                      'color': '{}'.format(instance.btncolor)})

    users = sorted(initusers,key=lambda k: k['bill'],reverse=True)

    return render_template('index.html', users=users)


@app.route('/login/<int:userid>',methods = ['GET'])
def login(userid):
    accountPayment(userid)
    userName = user.query.get(userid).username
    items = list()
    for instance in item.query:
        items.append({'name' :'{}'.format(instance.name),
                      'price': instance.price,
                      'itemid':'{}'.format(instance.itemid),
                      'count': len(history.query.filter(history.userid == userid ).filter(history.itemid == instance.itemid).filter(history.paid == False).all())})

    currbill = getcurrbill(userid)

    if currbill==None:
        currbill = 0

    return render_template('choices.html',
                           currbill = currbill,
                           chosenuser = userName,
                           userid = userid,
                           items = items
                           )

@app.route('/change/<int:userid>')
def change(userid):

    itemid = request.args.get('itemid')
    curuser = user.query.get(userid)
    curitem = item.query.get(itemid)
    userPurchase = history(curuser,curitem,curitem.price)

    db.session.add(userPurchase)
    db.session.commit()

    return redirect(url_for('login',userid=userid))

def build_sample_db():

    db.drop_all()
    db.create_all()

    name = [
        'Wilhelm Kackebart', 'Franz Powischer', 'Berta Haufen', 'Fritz Sabbert']
    email = [
        'wilhelm@kackebart.de', 'franz@powischer.de', 'berta@haufen.de', 'fritz@sabbert.de']

    for i in range(len(name)):
        newuser = user(username='{}'.format(name[i]),email = '{}'.format(email[i]))
        #newuser.username = name[i]
        #newuser.email = email[i]
        db.session.add(newuser)

    itemname = ['Coffee','Water','Snacks','Cola']
    price   = [0.5,0.9,0.6,0.3]

    for i in range(len(name)):
        newitem = item(name='{}'.format(itemname[i]),price = '{}'.format(price[i]))
       # newitem.name = itemname[i]
        #newitem.price = price[i]
        db.session.add(newitem)

    newadmin = coffeeadmin(name='admin',password='secretpassword')
    db.session.add(newadmin)

    db.session.commit()
    return


if __name__ == "__main__":
 #   app_dir = os.path.realpath(os.path.dirname(__file__))
 #   database_path = os.path.join(app_dir, 'TestDB.db')
 #   if not os.path.exists(database_path):
 #       print('Create new test database')
    #build_sample_db()


    app.run(debug=True)

