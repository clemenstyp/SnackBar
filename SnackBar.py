# coding: utf-8
import os, tablib, random
from flask import Flask, redirect,url_for,render_template,request, send_from_directory,current_app, safe_join, flash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin,expose,helpers,AdminIndexView, BaseView
from flask_admin.base import MenuLink
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
import flask_login as loginflask
from wtforms import form, fields, validators
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.pool import SingletonThreadPool
from jinja2 import Markup
from hashlib import md5
from math import sqrt
from sendEmail import Bimail
import time
import csv
from werkzeug.utils import secure_filename

from depot.manager import DepotManager

databaseName = 'CoffeeDB.db'
url = 'sqlite:///' + databaseName
engine = create_engine(url,  connect_args={'check_same_thread':False}, poolclass=SingletonThreadPool)
Session = sessionmaker(bind=engine)
session = Session()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = '123456790'
app.config['STATIC_FOLDER'] = 'static'
app.config['IMAGE_FOLDER'] = 'static/images'
app.config['ICON_FOLDER'] = 'static/icons'
app.config['DEBUG'] = False


db = SQLAlchemy(app)



def settingsFor(key):
    dbEntry = db.session.query(settings).filter_by(key=key).first()
    if dbEntry is None:
        return ''
    else:
        return dbEntry.value

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
    date = db.Column(db.DateTime)

    def __init__(self,user=None,item=None,price=0,date = None):
        self.user = user
        self.item = item
        self.price = price

        if date is None:
            date = datetime.now()
        self.date = date

    def __repr__(self):
        return 'User {} bought {} for {} on the {}'.format(self.user,self.item,self.price,self.date)

class inpayment(db.Model):

    paymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))
    user = db.relationship('user', backref=db.backref('inpayment', lazy='dynamic'))

    amount = db.Column(db.Float)
    date = db.Column(db.DateTime)
    notes = db.Column(db.String(120))

    def __init__(self, user=None, amount=None, date=None, notes=None):
        self.userid = user
        self.amount = amount
        self.notes = notes

        if date is None:
            date = datetime.now()
        self.date = date

    def __repr__(self):
        return 'User {} paid {} on the {}'.format(self.userid, self.amount, self.date)


class user(db.Model):
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstName = db.Column(db.String(80),nullable=False,default = '')
    lastName = db.Column(db.String(80),nullable=False,default = '')
    imageName = db.Column(db.String(240))
    email = db.Column(db.String(120),nullable=False,default = '')
    hidden = db.Column(db.Boolean)

    def __init__(self, firstName='', lastName='', email='', imageName= ''):
        if not firstName:
            firstName = ''
        if not lastName:
            lastName = ''
        if not imageName:
            imageName = ''
        if not email:
            email = 'example@example.org'

        self.hidden = False
        self.firstName = firstName
        self.lastName = lastName
        self.imageName = imageName
        self.email = email



    def __repr__(self):
        return '{} {}'.format(self.firstName,self.lastName)

class item(db.Model):
    itemid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True,nullable=False,default = '')
    price = db.Column(db.Float)
    icon = db.Column(db.String(300))

    def __init__(self, name='', price=0):
        self.name = name
        self.price = price

    def __repr__(self):
        return self.name

class coffeeadmin(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True,nullable=False,default = '')
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

class settings(db.Model):
    settingsid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(80), unique=True)
    value = db.Column(db.String(600))

    def __init__(self, key='', value=''):
        if not key:
            key = ''
        if not value:
            value = ''

        self.key = key
        self.value = value

    def __repr__(self):
        return self.key


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
    currBillNew = db.session.query(func.sum(history.price)).\
                                filter(history.userid == userid).scalar()
    if currBillNew == None:
        currBillNew = 0

    # bill = history.query.filter(history.userid == userid).filter(history.paid == False)
    # currbill = 0

    # for entry in bill:
    #     currbill += entry.price

    return currBillNew

def getUsers():
    getUsers(false)

def getUsers(withLeader):

    initusers = list()
    allItems = item.query.filter(item.icon != None , item.icon != '', item.icon != ' ')
    allItemID = [int(instance.itemid) for instance in allItems]
    itemid = allItemID[0]

    for instance in user.query.filter(user.hidden != True):
        initusers.append({'firstName': '{}'.format(instance.firstName),
                          'lastName': '{}'.format(instance.lastName),
                          'imageName': '{}'.format(instance.imageName),
                          'id': '{}'.format(instance.userid),
                          'bgcolor': '{}'.format(button_background(instance.firstName + ' ' + instance.lastName)),
                          'fontcolor': '{}'.format(button_font_color(instance.firstName + ' ' + instance.lastName)),
                          'coffeeMonth': getunpaid(instance.userid,itemid),
                          'leader' : getLeaderData(instance.userid, not withLeader),
                              })
    return initusers

def getLeaderData(userid, skip):
    leaderInfo = list()
    if not skip:
        allItems = item.query.filter(item.icon != None, item.icon != '', item.icon != ' ')
        i = 0
        for aItem in allItems:
            leaderID = int(getLeader(aItem.itemid))
            if leaderID == userid:
                itemID = int(aItem.itemid)
                icon = str(aItem.icon)
                position = (-7 + (i * 34))
                leaderInfo.append({"itemID": itemID, "icon": icon, "position": position})
                i = i +1
    return leaderInfo

def getLeader(itemid):

    tmpQuery = db.session.query(user.userid, func.count(history.price)). \
        outerjoin(history, and_(user.userid == history.userid, history.itemid == itemid,
                                extract('month', history.date) == datetime.now().month,
                  extract('year', history.date) == datetime.now().year)). \
            group_by(user.userid).\
               order_by(func.count(history.price).desc()).first()


    return tmpQuery[0]

def getRank(userid, itemid):

    tmpQuery = db.session.query(user.userid, func.count(history.price)).\
                   outerjoin(history, and_(user.userid == history.userid,history.itemid == itemid,extract('month', history.date) == datetime.now().month,extract('year', history.date) == datetime.now().year)).\
                   group_by(user.userid).\
                   order_by(func.count(history.price).desc()).all()

    userID = [x[0] for x in tmpQuery]
    itemSUM = [x[1] for x in tmpQuery]

    idx = userID.index(userid)
    rank = idx+1

    if rank == len(userID):
        upperbound = itemSUM[idx-1] - itemSUM[idx]+1
        lowerbound = None
        # print(itemSUM[idx-1])
        # print(itemSUM[idx])

    elif rank == 1:
        upperbound = None
        lowerbound = itemSUM[idx] - itemSUM[idx+1]+1

        # print(itemSUM[idx])
        # print(itemSUM[idx+1])
    else:
        upperbound = itemSUM[idx-1] - itemSUM[idx]+1
        lowerbound = itemSUM[idx] - itemSUM[idx+1]+1
        # print(itemSUM[idx-1])
        # print(itemSUM[idx])
        # print(itemSUM[idx+1])


    return {'rank': rank,
            'upperbound' : upperbound,
            'lowerbound' : lowerbound}

def getunpaid(userid,itemid):

    nUnpaid = db.session.query(history).\
            filter(history.userid == userid).\
            filter(history.itemid == itemid). \
            filter(extract('month', history.date) == datetime.now().month). \
            filter(extract('year', history.date) == datetime.now().year) \
            .count()

    if nUnpaid == None:
        nUnpaid = 0

    return nUnpaid

def gettotal(userid,itemid):

    nUnpaid = db.session.query(history).\
            filter(history.userid == userid).\
            filter(history.itemid == itemid).count()

    if nUnpaid == None:
        nUnpaid = 0

    return nUnpaid


def getPayment(userid):

    totalPaymentNew = db.session.query(func.sum(inpayment.amount)).\
                        filter(inpayment.userid == userid).scalar()
    if totalPaymentNew == None:
        totalPaymentNew = 0

    return totalPaymentNew

def restBill(userid):

    currBill = getcurrbill(userid)
    totalPayment = getPayment(userid)

    restAmount = -currBill+totalPayment

    return restAmount

def makeXLSBill(filename,fullpath):
    #filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
    #                                        datetime.now().time().strftime('%H-%M-%S'))

    #fullpath = os.path.join(current_app.root_path, app.config['STATIC_FOLDER'])
    header = list()
    header.append('name')
    for entry in item.query:
        header.append('{}'.format(entry.name))
    header.append('bill')

    excelData = tablib.Dataset()
    excelData.headers = header

    for instance in user.query.filter(user.hidden != True):
        firstline = list()
        firstline.append('{} {}'.format(instance.firstName, instance.lastName))

        for record in item.query:
            firstline.append('{}'.format(getunpaid(instance.userid, record.itemid)))

        firstline.append('{0:.2f}'.format(restBill(instance.userid)))
        excelData.append(firstline)

    with open(os.path.join(fullpath, filename), 'wb') as f:
        f.write(excelData.xls)

    return

def button_background(user):
    """
        returns the background color based on the username md5
    """
    hash = md5(user.encode('utf-8')).hexdigest()
    hash_values = (hash[:8], hash[8:16], hash[16:24])
    background = tuple(int(value, 16) % 256 for value in hash_values)
    return '#%02x%02x%02x' % background

def button_font_color(user):
    """
        returns black or white according to the brightness
    """
    rCoef = 0.241
    gCoef = 0.691
    bCoef = 0.068
    hash = md5(user.encode('utf-8')).hexdigest()
    hash_values = (hash[:8], hash[8:16], hash[16:24])
    bg = tuple(int(value, 16) % 256 for value in hash_values)
    b = sqrt(rCoef * bg[0] ** 2 + gCoef * bg[1] ** 2 + bCoef * bg[2] ** 2)
    if b > 130:
        return '#%02x%02x%02x' % (0, 0, 0)
    else:
        return '#%02x%02x%02x' % (255, 255, 255)


class AnalyticsView(BaseView):

    @expose('/')
    def index(self):

        initusers = list()

        for instance in user.query.filter(user.hidden != True):

            initusers.append({'name': '{} {}'.format(instance.firstName,instance.lastName),
                          'userid':'{}'.format(instance.userid),
                          'bill': restBill(instance.userid)})

        users = sorted(initusers, key=lambda k: k['name'])

        return self.render('admin/test.html',users = users)

    @expose('/reminder/')
    def reminder(self):
        for aUser in user.query.filter(user.hidden != True):
            sendReminder(aUser)
        return redirect(url_for('admin.index'))


    @expose('/export/')
    def export(self):
        filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
                                                 datetime.now().time().strftime('%H-%M-%S'))

        fullpath = os.path.join(current_app.root_path, app.config['STATIC_FOLDER'])
        makeXLSBill(filename,fullpath)

        return send_from_directory(directory=fullpath, filename=filename, as_attachment=True)

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

class MyPaymentModelView(ModelView):
    can_create = True
    can_delete = False
    can_edit = False
    can_export = True
    form_excluded_columns = ('date')
    export_types = ['csv', 'xls']
    column_default_sort = ('date', True)
    column_filters = ('user', 'amount', 'date')
    list_template = 'admin/custom_list.html'

    def date_format(view, context, model, name):
        field = getattr(model, name)
        return field.strftime('%Y-%m-%d %H:%M')

    column_formatters = dict(date=date_format)

    def is_accessible(self):
        return loginflask.current_user.is_authenticated


    def page_sum(self, current_page):
        # this should take into account any filters/search inplace
        _query = self.session.query(inpayment).limit(self.page_size).offset(current_page * self.page_size)
        page_sum = sum([payment.amount for payment in _query])
        return '{0:.2f}'.format(page_sum)

    def total_sum(self):
        # this should take into account any filters/search inplace
        total_sum = self.session.query(func.sum(inpayment.amount)).scalar()
        return '{0:.2f}'.format(total_sum)

    def render(self, template, **kwargs):
        # we are only interested in the list page
        if template == 'admin/custom_list.html':
            # append a summary_data dictionary into kwargs
            _current_page = kwargs['page']
            kwargs['summary_data'] = [
                {'title': 'Page Total', 'amount': self.page_sum(_current_page)},
                {'title': 'Grand Total', 'amount': self.total_sum()},
            ]
            kwargs['summary_title'] = [{'title': ''}, {'title': 'Amount'},]
        return super(MyPaymentModelView, self).render(template, **kwargs)


class MyHistoryModelView(ModelView):
    can_create = True
    can_export = True
    can_delete = True
    can_edit = True
    export_types = ['csv', 'xls']
    column_descriptions = dict()
    column_labels = dict(user='Name')
    column_default_sort =  ('date', True)
    column_filters = ('name', 'item', 'date')
    form_args = dict(date=dict(default=datetime.now()),price=dict(default=0) )
    def date_format(view, context, model, name):
        field = getattr(model, name)
        if field is not None:
            return field.strftime('%Y-%m-%d %H:%M')
        else:
            return ""

    column_formatters = dict(date = date_format)

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

class MyUserModelView(ModelView):
    can_export = True
    export_types = ['csv', 'xls']
    form_excluded_columns = ('history','inpayment')
    column_descriptions = dict(
        firstName='Name of the corresponding person'
    )

    base_path = app.config['IMAGE_FOLDER']
    form_overrides = dict(imageName=FileUploadField)
    form_args = {
        'imageName': {
            'base_path': base_path
        }
    }
    column_labels = dict(firstName='First Name',
                         lastName = 'Last Name',
                         imageName='User Image')

    def is_accessible(self):
        return loginflask.current_user.is_authenticated


class MyItemModelView(ModelView):
    can_export = True
    export_types =['csv','xls']
    form_excluded_columns = ('items')

    base_path = app.config['ICON_FOLDER']
    form_overrides = dict(icon=FileUploadField)
    form_args = {
        'icon': {
            'base_path': base_path
        }
    }


    def is_accessible(self):
        return loginflask.current_user.is_authenticated

class MyAdminModelView(ModelView):
    can_export = False
    #can_delete = False
    column_exclude_list = ['password', ]

    form_excluded_columns = ('password')

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a regular text field.

    def scaffold_form(self):
        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(MyAdminModelView, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New Password".
        form_class.password2 = fields.PasswordField('New Password')

        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):

            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = model.password2
            #model.password = utils.encrypt_password(model.password2)

    def delete_model(self, model):
        if loginflask.current_user.id == model.id:
            flash('You cannot delete your own account.')
            return False
        else:
            return super(MyAdminModelView, self).delete_model(model)

class MySettingsModelView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False
    can_export = False
    column_editable_list = ['value']

    column_labels = dict(key='Name', value='Value')

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
admin = Admin(app, name = 'SnackBar Admin Page', index_view=MyAdminIndexView(), base_template='my_master.html')
admin.add_view(AnalyticsView(name='Bill', endpoint='bill'))
admin.add_view(MyPaymentModelView(inpayment, db.session, 'Inpayment'))
admin.add_view(MyUserModelView(user, db.session, 'User'))
admin.add_view(MyItemModelView(item, db.session,'Items'))
admin.add_view(MyHistoryModelView(history, db.session,'History'))
admin.add_view(MyAdminModelView(coffeeadmin, db.session,'Admins'))
admin.add_view(MySettingsModelView(settings, db.session,'Settings'))
admin.add_link(MenuLink(name='Snack Bar', url='/'))

current_sorting = ""

@app.route('/')
def initial():
    global current_sorting
    initusers = getUsers(true)

    if current_sorting == "az":
        users = sorted(initusers, key=lambda k: k['firstName'])
    elif current_sorting == "za":
        users = sorted(initusers, key=lambda k: k['firstName'])
        users.reverse()
    elif current_sorting == "coffee19":
        users = sorted(initusers, key=lambda k: k['coffeeMonth'])
    elif current_sorting == "coffee91":
        users = sorted(initusers, key=lambda k: k['coffeeMonth'])
        users.reverse()
    else:
        current_sorting = "az"
        users = sorted(initusers, key=lambda k: k['firstName'])


    return render_template('index.html', users=users, current_sorting=current_sorting)




@app.route('/sort/<sorting>')
def sort(sorting):
    global current_sorting
    current_sorting = sorting
    return redirect(url_for('initial'))


@app.route('/adduser', methods=('GET', 'POST'))
def adduser():

    if request.method == 'POST':
        firstNameError = False
        firstName = ''
        if request.form['firstname'] == None or request.form['firstname'] == '' :
            firstNameError = true
        else:
            firstName = request.form['firstname']

        lastNameError = False
        lastName = ''
        if request.form['lastname'] == None or request.form['lastname'] == '':
            lastNameError = true
        else:
            lastName = request.form['lastname']

        from email.utils import parseaddr
        emailError = False
        email = ''
        if request.form['email'] == None or request.form['email'] == '':
            emailError = true
        else:
            email = parseaddr(request.form['email'])[1]
            if email == '':
                emailError = true


        if not firstNameError and not lastNameError and not emailError:
            with app.app_context():
                filename = ''
                if 'image'  in request.files:
                    file = request.files['image']
                    if file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        fullPath = os.path.join(app.config['IMAGE_FOLDER'], filename)
                        file.save(fullPath)

                newUser = user(firstName=firstName, lastName=lastName, email=email, imageName= filename)

                db.session.add(newUser)
                db.session.commit()
                sendEmailNewUser(newUser)

                return redirect(url_for('initial'))
        else:
            return render_template('adduser.html', firstNameError=firstNameError, firstName=firstName, lastNameError=lastNameError, lastName=lastName,
                                   emailError=emailError, email=email)
    else:
        return render_template('adduser.html', firstNameError=False, firstName='', lastNameError=False, lastName='',emailError=False, email='' )


def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/image/')
def defaultImage():
    return image(None)


@app.route('/image/<filename>')
def image(filename):
    return imageFromFolder(filename, app.config['IMAGE_FOLDER'], "static/unknown_image.png")

@app.route('/icon/')
def defaultIcon():
    return icon(None)

@app.route('/icon/<icon>')
def icon(icon):
    return imageFromFolder(icon, app.config['ICON_FOLDER'], "static/unknown_icon.svg")


def imageFromFolder(filename, imageFolder, defaultImage):
    if filename is None:
        return send_from_directory(directory=current_app.root_path, filename=defaultImage, as_attachment=False)

    fullpath = os.path.join(current_app.root_path, imageFolder)

    fullFilePath = safe_join(fullpath, filename)
    if not os.path.isabs(fullFilePath):
        fullFilePath = os.path.join(current_app.root_path, fullFilePath)
    try:
        if not os.path.isfile(fullFilePath):
            return send_from_directory(directory=current_app.root_path, filename=defaultImage, as_attachment=False)
    except (TypeError, ValueError):
        pass

    return send_from_directory(directory=fullpath, filename=filename, as_attachment=False)
    #return redirect(url)


@app.route('/user/<int:userid>',methods = ['GET'])
def userPage(userid):

    userName = '{} {}'.format(user.query.get(userid).firstName,user.query.get(userid).lastName)
    items = list()

    for instance in item.query:
        rankInfo = getRank(userid, instance.itemid)
        items.append({'name'  : '{}'.format(instance.name),
                      'price' : instance.price,
                      'itemid': '{}'.format(instance.itemid),
                      'icon' : '{}'.format(instance.icon),
                      'count' : getunpaid(userid,instance.itemid),
                      'total': gettotal(userid, instance.itemid),
                      'rank'  : rankInfo['rank'],
                      'ub'    : rankInfo['upperbound'],
                      'lb'    : rankInfo['lowerbound']})

    noUsers = user.query.filter(user.hidden != True).count()
    currbill = restBill(userid)

    return render_template('choices.html',
                           currbill = currbill,
                           chosenuser = userName,
                           userid = userid,
                           items = items,
                           noOfUsers = noUsers,
                           )

def sendEmailNewUser(curuser):
    if curuser.email:
        mymail = Bimail('SnackBar User Created', ['{}'.format(curuser.email)])
        mymail.sendername = settingsFor('mailSender')
        mymail.sender = settingsFor('mailSender')
        mymail.servername = settingsFor('mailServer')
        # start html body. Here we add a greeting.
        mymail.htmladd(
            'Hallo {} {},<br><br>ein neuer Benutzer wurde mit dieser E-Mail Adresse erstellt. Solltest du diesen Acocunt nicht erstellt habe, melde dich bitte bei {}.<br><br>Ciao,<br>SnackBar Team [{}]<br><br><br><br>---------<br><br><br><br>Hello {} {},<br><br>a new user has been created with this mail address. If you have not created this Acocunt, please contact {}.<br><br>Ciao,<br>SnackBar Team [{}]'.format(
                curuser.firstName, curuser.lastName, settingsFor('snackAdmin'), settingsFor('snackAdmin'), curuser.firstName,
                curuser.lastName, settingsFor('snackAdmin'), settingsFor('snackAdmin')))
        # Further things added to body are separated by a paragraph, so you do not need to worry about newlines for new sentences
        # here we add a line of text and an html table previously stored in the variable
        # add image chart title
        # attach another file
        # mymail.htmladd('Ciao,<br>SnackBar Team [Clemens Putschli (C5-315)]')
        # mymail.addattach([os.path.join(fullpath, filename)])
        # send!
        # print(mymail.htmlbody)
        mymail.send()

def sendReminder(curuser):
    if curuser.email:
        curnbilFloat = restBill(curuser.userid)
        minimumBalance = float(settingsFor('minimumBalance'))
        if curnbilFloat <= minimumBalance:
            currbill = '{0:.2f}'.format(restBill(curuser.userid))
            #print(instance.firstName)
            #print(currbill)
            mymail = Bimail('SnackBar Reminder', ['{}'.format(curuser.email)])
            mymail.sendername = settingsFor('mailSender')
            mymail.sender = settingsFor('mailSender')
            mymail.servername = settingsFor('mailServer')
            # start html body. Here we add a greeting.
            mymail.htmladd('Hallo {} {},<br><br>du hast nur noch wenig Geld auf deinem SnackBar Konto ({} €). Zahle bitte ein bisschen Geld ein, damit wir wieder neue Snacks kaufen können!<br><br>Ciao,<br>SnackBar Team [{}]<br><br><br><br>---------<br><br><br><br>Hello {} {},<br><br>your SnackBar balance is very low ({} €). Please top it up with some money!<br><br>Ciao,<br>SnackBar Team [{}]'.format(curuser.firstName,curuser.lastName, currbill, settingsFor('snackAdmin'),  curuser.firstName,curuser.lastName, currbill, settingsFor('snackAdmin')))
            # Further things added to body are separated by a paragraph, so you do not need to worry about newlines for new sentences
            # here we add a line of text and an html table previously stored in the variable
            # add image chart title
            # attach another file
            # mymail.htmladd('Ciao,<br>SnackBar Team [Clemens Putschli (C5-315)]')
            #mymail.addattach([os.path.join(fullpath, filename)])
            # send!
            #print(mymail.htmlbody)
            mymail.send()

def sendEmail(curuser, curitem):
    if curuser.email:

        currbill = '{0:.2f}'.format(restBill(curuser.userid))
        #print(instance.firstName)
        #print(currbill)
        mymail = Bimail('SnackBar++ ({} {})'.format(curuser.firstName, curuser.lastName), ['{}'.format(curuser.email)])
        mymail.sendername = settingsFor('mailSender')
        mymail.sender = settingsFor('mailSender')
        mymail.servername = settingsFor('mailServer')
        # start html body. Here we add a greeting.

        today = datetime.now().strftime('%Y-%m-%d %H:%M')
        mymail.htmladd(
            'Hallo {} {}, <br>SnackBar hat gerade "{}" ({} €) für dich GEBUCHT! <br><br> Dein Guthaben beträgt jetzt {} € <br><br>'.format(
                curuser.firstName, curuser.lastName, curitem.name, curitem.price, currbill))
        mymail.htmladd('Ciao,<br>SnackBar Team [{}]'.format(settingsFor('snackAdmin')))
        mymail.htmladd('<br><br>---------<br><br>')
        mymail.htmladd('Hello {} {}, <br>SnackBar has just REGISTERED an other {} ({} €) for you! <br><br> Your balance is now {} € <br><br> '.format(curuser.firstName,curuser.lastName,curitem.name,curitem.price, currbill))
        # Further things added to body are separated by a paragraph, so you do not need to worry about newlines for new sentences
        # here we add a line of text and an html table previously stored in the variable
        # add image chart title
        # attach another file
        mymail.htmladd('Ciao,<br>SnackBar Team [{}]'.format(settingsFor('snackAdmin')))

        mymail.htmladd('<br><br>---------<br>Registered at: {}'.format(today))


        #mymail.addattach([os.path.join(fullpath, filename)])
        # send!
        #print(mymail.htmlbody)
        mymail.send()



@app.route('/change/<int:userid>')
def change(userid):

    itemid = request.args.get('itemid')
    curuser = user.query.get(userid)
    curitem = item.query.get(itemid)
    userPurchase = history(curuser,curitem,curitem.price)

    db.session.add(userPurchase)
    db.session.commit()

    sendEmail(curuser, curitem)
    return redirect(url_for('userPage',userid = userid))

@app.route('/analysis')
def analysis():
    from analysisUtils import main
    content, tagsHours = main()
    return render_template('analysis.html', content = content, tagsHours = tagsHours)


def build_sample_db():
    db.drop_all()
    db.create_all()

    with open('userList.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            newuser = user(firstName='{}'.format(row['FirstName']),
                           lastName='{}'.format(row['LastName']),
                           imageName='{}'.format(row['ImageName']),
                           email='{}'.format(row['email']))
            db.session.add(newuser)
            initialBalance = '{}'.format(row['InitialBalance'])
            try:
                initialBalanceFloat = float(initialBalance)
                if initialBalanceFloat != 0:
                    initialPayment = inpayment(amount=initialBalance)
                    initialPayment.user = newuser
                    db.session.add(initialPayment)
            except:
                pass






    '''
    name = [
        'Wilhelm Müller', 'Franz Meier', 'Berta Schmitt', 'Fritz Hase']
    email = [
        'wilhelm@mueller.de', 'franz@meier.de', 'berta@schmitt.de', 'fritz@hase.de']

    for i in range(len(name)):
        newuser = user(username='{}'.format(name[i]),email = '{}'.format(email[i]))
        #newuser.username = name[i]
        #newuser.email = email[i]
    '''


    itemname = ['Coffee','Water','Snacks','Cola']
    price   = [0.2,0.55,0.2,0.4]

    for i in range(len(itemname)):
        newitem = item(name='{}'.format(itemname[i]),price = '{}'.format(price[i]))
        newitem.icon = "item" + str(i+1) + ".svg"
       # newitem.name = itemname[i]
        #newitem.price = price[i]
        db.session.add(newitem)

    newadmin = coffeeadmin(name = 'admin', password = 'admin')
    db.session.add(newadmin)

    db.session.commit()
    return


def set_default_settings():
    with open('defaultSettings.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = '{}'.format(row['key'])
            dbEntry = db.session.query(settings).filter_by(key=key).first()
            if dbEntry is None:
                newsettingitem = settings(key='{}'.format(row['key']), value='{}'.format(row['value']))
                db.session.add(newsettingitem)


    db.session.commit()


def send_reminder_to_all():
    try:
        for aUser in user.query.filter(user.hidden != True):
            sendReminder(aUser)
    except:
        pass


import schedule
import time
import threading
from flaskrun import flaskrun

def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":

    schedule.every().monday.at("10:30").do(send_reminder_to_all)
    schedule_thread = threading.Thread(target=run_schedule).start()

    if not os.path.isfile(databaseName):
        build_sample_db()

    set_default_settings()
    # app.run()
    #app.run(host='0.0.0.0', port=5000, debug=False)
    flaskrun(app)


