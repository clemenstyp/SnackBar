# coding: utf-8
import csv
import math
import os
import threading
import time
import string
import random
from datetime import date, datetime, timedelta
from hashlib import md5
from math import sqrt
from collections import Counter
import traceback

import flask_login as loginflask
import schedule
import tablib
from flask import Flask, redirect, url_for, render_template, request, send_from_directory, current_app, flash, Response
from flask_admin import Admin, expose, helpers, AdminIndexView, BaseView
from flask_admin.base import MenuLink
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy.sql import func
# noinspection PyPackageRequirements
from werkzeug.utils import secure_filename, safe_join
# noinspection PyPackageRequirements
from wtforms import form, fields, validators
import requests
from flaskrun import flaskrun, load_options
from sendEmail import Bimail
# import code for encoding urls and generating md5 hashes
import urllib, hashlib
import optparse
import json
import paho.mqtt.publish as mqtt_publish
import logging
from logging.handlers import SMTPHandler
import urllib.parse

app = Flask(__name__)

databaseName = 'data/CoffeeDB.db'
url = f"sqlite:///{app.root_path}/{databaseName}"
engine = create_engine(url, connect_args={'check_same_thread': False}, poolclass=SingletonThreadPool)
Session = sessionmaker(bind=engine)
session = Session()

# Set up the command-line options
options = load_options()

app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = '123456790' + options.url_prefix
app.config['STATIC_FOLDER'] = 'static'
app.config['IMAGE_FOLDER'] = 'static/images'
app.config['ICON_FOLDER'] = 'static/icons'
app.config['DEBUG'] = False
app.config['SESSION_COOKIE_PATH'] = '/'

db = SQLAlchemy(app)



if not os.path.exists(app.config['IMAGE_FOLDER']):
    os.makedirs(app.config['IMAGE_FOLDER'])




#image cache for gravatar images
imageCache = {}

def settings_for(key):
    with app.app_context():
        db_entry = db.session.query(Settings).filter_by(key=key).first()
        if db_entry is None:
            return ''
        else:
            return db_entry.value


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


class History(db.Model):
    historyid = db.Column(db.Integer, primary_key=True, autoincrement=True)

    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))
    user = db.relationship('User', backref=db.backref('history', lazy='dynamic'))
    # user = db.relationship('User', foreign_keys=userid)

    itemid = db.Column(db.Integer, db.ForeignKey('item.itemid'))
    item = db.relationship('Item', backref=db.backref('items', lazy='dynamic'))
    # item = db.relationship('Item', foreign_keys=itemid)

    price = db.Column(db.Float)
    date = db.Column(db.DateTime)

    def __init__(self, user=None, item=None, price=0, date=None):
        self.user = user
        self.item = item
        self.price = price

        if date is None:
            date = datetime.now()
        self.date = date

    def __repr__(self):
        return 'User {} bought {} for {} on the {}'.format(self.user, self.item, self.price, self.date)


class Inpayment(db.Model):
    paymentid = db.Column(db.Integer, primary_key=True, autoincrement=True)

    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))
    user = db.relationship('User', backref=db.backref('inpayment', lazy='dynamic'))
    # user = db.relationship('User', foreign_keys=userid)

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


class User(db.Model):
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstName = db.Column(db.String(80), nullable=False, default='')
    lastName = db.Column(db.String(80), nullable=False, default='')
    imageName = db.Column(db.String(240))
    email = db.Column(db.String(120), nullable=False, default='')
    hidden = db.Column(db.Boolean)

    def __init__(self, firstname='', lastname='', email='', imagename=''):
        if not firstname:
            firstname = ''
        if not lastname:
            lastname = ''
        if not imagename:
            imagename = ''
        if not email:
            email = 'example@example.org'

        self.hidden = False
        self.firstName = firstname
        self.lastName = lastname
        self.imageName = imagename
        self.email = email

    def __repr__(self):
        return '{} {}'.format(self.firstName, self.lastName)


class Item(db.Model):
    itemid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable=False, default='')
    price = db.Column(db.Float)
    icon = db.Column(db.String(300))

    def __init__(self, name='', price=0):
        self.name = name
        self.price = price

    def __repr__(self):
        return self.name


class Coffeeadmin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, default='')
    password = db.Column(db.String(64))
    send_bill = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(120), default='')

    # Flask-Login integration
    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.id


class Settings(db.Model):
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
    login = fields.StringField(validators=[validators.DataRequired()])
    password = fields.PasswordField(validators=[validators.DataRequired()])

    # noinspection PyUnusedLocal
    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid User')

        # we're comparing the plaintext pw with the the hash from the db
        if user.password != self.password.data:
            # to compare plain text passwords use
            # if User.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        with app.app_context():
            return db.session.query(Coffeeadmin).filter_by(name=self.login.data).first()


# noinspection PyUnusedLocal
class RegistrationForm(form.Form):
    login = fields.StringField(validators=[validators.DataRequired()])
    email = fields.StringField()
    password = fields.PasswordField(validators=[validators.DataRequired()])

    def validate_login(self, field):
        with app.app_context():
            if db.session.query(Coffeeadmin).filter_by(name=self.login.data).count() > 0:
                raise validators.ValidationError('Duplicate username')


def init_login():
    login_manager = loginflask.LoginManager()
    login_manager.init_app(app)

    # Create User loader function
    @login_manager.user_loader
    def load_user(user_id):
        with app.app_context():
            return db.session.get(Coffeeadmin, user_id)


def getcurrbill(userid):
    with app.app_context():
        curr_bill_new = db.session.query(func.sum(History.price)). \
            filter(History.userid == userid).scalar()
        if curr_bill_new is None:
            curr_bill_new = 0

        # bill = History.query.filter(History.userid == userid).filter(History.paid == False)
        # currbill = 0

        # for entry in bill:
        #     currbill += entry.price

        return curr_bill_new



def get_users_with_leaders():
    initusers = list()
    with app.app_context():
        all_items = Item.query.filter(Item.icon is not None, Item.icon != '', Item.icon != ' ')
        all_items_id = [int(instance.itemid) for instance in all_items]
        if len(all_items_id) > 0:
            itemid = all_items_id[0]
        else:
            itemid = ''

        leader_data = get_all_leader_data()

        for instance in User.query.filter(User.hidden.is_(False)):
            initusers.append({'firstName': '{}'.format(instance.firstName),
                                  'lastName': '{}'.format(instance.lastName),
                                  'imageName': '{}'.format(instance.imageName),
                                  'id': '{}'.format(instance.userid),
                                  'bgcolor': '{}'.format(button_background(instance.firstName + ' ' + instance.lastName)),
                                  'fontcolor': '{}'.format(button_font_color(instance.firstName + ' ' + instance.lastName)),
                                  'coffeeMonth': get_unpaid(instance.userid, itemid, leader_data),
                                  'leader': get_leader(instance.userid, leader_data),
                                   'email': '{}'.format(instance.email),
                                  })
    return initusers


def get_all_leader_data():
    leader_data = {}
    with app.app_context():
        all_items = Item.query.filter(Item.icon is not None, Item.icon != '', Item.icon != ' ')
        for aItem in all_items:
            leader_ids = get_leaders_from_database(aItem.itemid)

            item_data = {'leader_ids': leader_ids, 'icon' : aItem.icon}
            leader_data[aItem.itemid]= item_data



    return leader_data


def get_leaders_from_database(itemid):
    with app.app_context():
        tmp_query = db.session.query(User.userid, func.count(History.price), func.max(History.date))
        tmp_query = tmp_query.outerjoin(History, and_(User.userid == History.userid, History.itemid == itemid,
                                                      extract('month', History.date) == datetime.now().month,
                                                      extract('year', History.date) == datetime.now().year))
        tmp_query = tmp_query.group_by(User.userid)
        tmp_query = tmp_query.order_by(func.count(History.price).desc())
        tmp_query = tmp_query.order_by(History.date)
        tmp_query = tmp_query.all()


        return tmp_query

def get_unpaid(userid, itemid, leader_data):
    returnValue = 0
    if itemid in leader_data:
        item_data = leader_data[itemid]['leader_ids']

        user_ids = [x[0] for x in item_data]
        item_sums = [x[1] for x in item_data]

        try:
            idx = user_ids.index(userid)
            returnValue = item_sums[idx]
        except (TypeError, ValueError):
            pass



    return returnValue



def get_leader(userid, leader_data):
    leader_info = list()
    i = 0
    for itemid in sorted(leader_data.keys()):
        item_data = leader_data[itemid]
        item_leader = item_data['leader_ids']
        if len(item_leader) > 0:
            winner = item_leader[0]
            winner_id = winner[0]
            winner_count = winner[1]
            if int(winner_id) == userid and winner_count > 0:
                item_id = int(itemid)
                icon_file = str(item_data['icon'])
                position = (-7 + (i * 34))
                leader_info.append({"item_id": item_id, "icon": icon_file, "position": position})
                i = i + 1

    return leader_info



def get_rank(userid, itemid, leader_data):
    rank = 0
    lowerbound = None
    upperbound = None
    if itemid in leader_data:
        item_data = leader_data[itemid]['leader_ids']

        user_id = [x[0] for x in item_data]
        item_sum = [x[1] for x in item_data]

        idx = user_id.index(userid)
        rank = idx + 1

        if rank == len(user_id):
            upperbound = item_sum[idx - 1] - item_sum[idx] + 1
            lowerbound = None

        elif rank == 1:
            upperbound = None
            lowerbound = item_sum[idx] - item_sum[idx + 1] + 1

        else:
            upperbound = item_sum[idx - 1] - item_sum[idx] + 1
            lowerbound = item_sum[idx] - item_sum[idx + 1] + 1

    return {'rank': rank,
            'upperbound': upperbound,
            'lowerbound': lowerbound}





def get_total(userid, itemid):
    with app.app_context():
        n_unpaid = db.session.query(History). \
            filter(History.userid == userid). \
            filter(History.itemid == itemid).count()

        if n_unpaid is None:
            n_unpaid = 0

        return n_unpaid


def get_payment(userid):
    with app.app_context():
        total_payment_new = db.session.query(func.sum(Inpayment.amount)). \
            filter(Inpayment.userid == userid).scalar()
        if total_payment_new is None:
            total_payment_new = 0

        return total_payment_new


def rest_bill(userid):
    curr_bill = getcurrbill(userid)
    total_payment = get_payment(userid)

    rest_amount = -curr_bill + total_payment

    return rest_amount


def make_xls_bill(filename, fullpath):
    with app.app_context():
        # filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
        #                                        datetime.now().time().strftime('%H-%M-%S'))

        # fullpath = os.path.join(current_app.root_path, app.config['STATIC_FOLDER'])
        header = list()
        header.append('name')
        for entry in Item.query:
            header.append('{}'.format(entry.name))
        header.append('bill')

        excel_data = tablib.Dataset()
        excel_data.headers = header

        leader_data = get_all_leader_data()

        for instance in User.query.filter(User.hidden.is_(False)):
            firstline = list()
            firstline.append('{} {}'.format(instance.firstName, instance.lastName))

            for record in Item.query:
                firstline.append('{}'.format(get_unpaid(instance.userid, record.itemid, leader_data)))

            firstline.append('{0:.2f}'.format(rest_bill(instance.userid)))
            excel_data.append(firstline)

        with open(os.path.join(fullpath, filename), 'wb') as f:
            f.write(excel_data.xls)

        return


def button_background(user):
    """
        returns the background color based on the username md5
    """
    hash_string = md5(user.encode('utf-8')).hexdigest()
    hash_values = (hash_string[:8], hash_string[8:16], hash_string[16:24])
    background = tuple(int(value, 16) % 256 for value in hash_values)
    return '#%02x%02x%02x' % background


def button_font_color(user):
    """
        returns black or white according to the brightness
    """
    r_coef = 0.241
    g_coef = 0.691
    b_coef = 0.068
    hash_string = md5(user.encode('utf-8')).hexdigest()
    hash_values = (hash_string[:8], hash_string[8:16], hash_string[16:24])
    bg = tuple(int(value, 16) % 256 for value in hash_values)
    b = sqrt(r_coef * bg[0] ** 2 + g_coef * bg[1] ** 2 + b_coef * bg[2] ** 2)
    if b > 130:
        return '#%02x%02x%02x' % (0, 0, 0)
    else:
        return '#%02x%02x%02x' % (255, 255, 255)


class MyBillView(BaseView):

    @expose('/')
    def index(self):

        initusers = list()
        total_bill = 0
        total_cash = db.session.query(func.sum(Inpayment.amount)).scalar()
        if total_cash is None:
            total_cash = 0

        for instance in User.query.filter(User.hidden.is_(False)):
            bill = rest_bill(instance.userid)
            total_bill += bill
            initusers.append({'name': '{} {}'.format(instance.firstName, instance.lastName),
                              'userid': '{}'.format(instance.userid),
                              'bill': bill})

        users = sorted(initusers, key=lambda k: k['name'])

        init_hidden_users = list()
        hidden_total_bill = 0
        for instance in User.query.filter(User.hidden.is_(True)):
            bill = rest_bill(instance.userid)
            hidden_total_bill += bill
            init_hidden_users.append({'name': '{} {}'.format(instance.firstName, instance.lastName),
                              'userid': '{}'.format(instance.userid),
                              'bill': bill})

        hidden_users = sorted(init_hidden_users, key=lambda k: k['bill'])

        return self.render('admin/bill.html', users=users, hidden_users=hidden_users, hidden_total_bill=hidden_total_bill, total_bill=total_bill, total_cash=total_cash, total_sum=(total_cash - total_bill))

    @expose('/reminder/')
    def reminder(self):
        for aUser in User.query.filter(User.hidden.is_(False)):
            send_reminder(aUser)
        return redirect(url_for('admin.index'))

    @expose('/export/')
    def export(self):
        filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
                                                 datetime.now().time().strftime('%H-%M-%S'))

        fullpath = os.path.join(current_app.root_path, app.config['STATIC_FOLDER'])
        make_xls_bill(filename, fullpath)

        return send_from_directory(directory=fullpath, path=filename, as_attachment=True)

    def is_accessible(self):
        return loginflask.current_user.is_authenticated


def get_total_bill():
    def nextMonth(currentMonth):
        if currentMonth.month == 12:  # New year
            return date(currentMonth.year + 1, 1, 1)
        else:
            return date(currentMonth.year, currentMonth.month + 1, 1)

    def prevMonth(currentMonth):
        if currentMonth.month == 1:  # New year
            return date(currentMonth.year - 1, 12, 1)
        else:
            return date(currentMonth.year, currentMonth.month - 1, 1)

    def months_between(date_start, date_end):
        months = []

        # Make sure start_date is smaller than end_date
        if date_start > date_end:
            tmp = date_start
            date_start = date_end
            date_end = tmp

        tmp_date = date_start
        while tmp_date.month <= date_end.month or tmp_date.year < date_end.year:
            months.append(
                tmp_date)  # Here you could do for example: months.append(datetime.datetime.strftime(tmp_date, "%b '%y"))
            tmp_date = nextMonth(tmp_date)

        return months

    with app.app_context():
        currentDay = datetime.now()
        newestDate = nextMonth(date(currentDay.year, currentDay.month, currentDay.day))
        oldestDate = prevMonth(newestDate)

        for instance in Inpayment.query.order_by(Inpayment.date).limit(1):
            oldestDateInpayment = date(instance.date.year, instance.date.month, 1)
            if oldestDateInpayment < oldestDate:
                oldestDate = oldestDateInpayment

        for instance in History.query.order_by(History.date).limit(1):
            oldestDateHistory = date(instance.date.year, instance.date.month, 1)
            if oldestDateHistory < oldestDate:
                oldestDate = oldestDateHistory

        total_cash = 0
        total_open = 0
        accounting = list()

        for month in months_between(oldestDate, newestDate):
            total_open = 0

            previousMonth = prevMonth(month)
            for instance in Inpayment.query.filter(Inpayment.date.between(previousMonth, month)):
                total_cash += instance.amount

            for instance in User.query.filter(User.hidden.is_(False)):
                curr_bill = 0
                for historyInstance in History.query.filter(
                        and_(History.date.between(oldestDate, month), History.userid == instance.userid)):
                    curr_bill += historyInstance.price

                total_payment = 0
                for inpaymentInstance in Inpayment.query.filter(
                        and_(Inpayment.date.between(oldestDate, month), Inpayment.userid == instance.userid)):
                    total_payment += inpaymentInstance.amount

                total_open -= -curr_bill + total_payment

            accounting.append({'name': '{}'.format(previousMonth.strftime('%B %Y')),
                               'from_date': '{}'.format(previousMonth),
                               'to_date': '{}'.format(month),
                               'cash': total_cash,
                               'open': total_open,
                               'sum': (total_cash + total_open)})

        return accounting, total_cash

class MyAccountingView(BaseView):

    @expose('/')
    def index(self):

        accounting, total_cash, total_open = get_total_bill()

        return self.render('admin/accounting.html', data=reversed(accounting), total_cash=total_cash, total_open=total_open, total_sum=(total_cash + total_open))


    def is_accessible(self):
        return loginflask.current_user.is_authenticated




class MyPaymentModelView(ModelView):
    can_create = True
    can_delete = False
    can_edit = True
    can_export = True
    form_excluded_columns = 'date'
    export_types = ['csv']
    column_descriptions = dict()
    column_labels = dict(user='Name')
    column_default_sort = ('date', True)
    column_filters = ('user', 'amount', 'date')
    list_template = 'admin/custom_list.html'

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def date_format(self, context, model, name):
        field = getattr(model, name)
        if field is not None:
            return field.strftime('%Y-%m-%d %H:%M')
        else:
            return ""

    column_formatters = dict(date=date_format)

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

    def page_sum(self, current_page):
        with app.app_context():
            # this should take into account any filters/search inplace
            #_query = self.session.query(Inpayment).limit(self.page_size).offset(current_page * self.page_size)
            #page_sum = sum([payment.amount for payment in _query])

            view_args = self._get_list_extra_args()
            # Map column index to column name
            sort_column = self._get_column_by_idx(view_args.sort)
            if sort_column is not None:
                sort_column = sort_column[0]

            # Get page size
            page_size = view_args.page_size or self.page_size
            count, data = self.get_list(current_page, sort_column, view_args.sort_desc,
                                        view_args.search, view_args.filters, page_size=page_size)

            page_sum = 0
            for payment in data:
                page_sum += payment.amount

            if page_sum is None:
                page_sum = 0
            return '{0:.2f}'.format(page_sum)

    def total_sum(self):
        with app.app_context():
            # this should take into account any filters/search inplace
            total_sum = self.session.query(func.sum(Inpayment.amount)).scalar()
            if total_sum is None:
                total_sum = 0
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
            kwargs['summary_title'] = [{'title': ''}, {'title': 'Amount'}, ]
        return super(MyPaymentModelView, self).render(template, **kwargs)


class MyHistoryModelView(ModelView):
    can_create = True
    can_export = True
    can_delete = True
    can_edit = True
    export_types = ['csv']
    column_descriptions = dict()
    column_labels = dict(user='Name')
    column_default_sort = ('date', True)
    column_filters = ('user', 'item', 'date')
    form_args = dict(date=dict(default=datetime.now()), price=dict(default=0))

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def date_format(self, context, model, name):
        field = getattr(model, name)
        if field is not None:
            return field.strftime('%Y-%m-%d %H:%M')
        else:
            return ""

    column_formatters = dict(date=date_format)

    def is_accessible(self):
        return loginflask.current_user.is_authenticated


class MyUserModelView(ModelView):
    can_export = True
    export_types = ['csv']
    column_exclude_list = ['history', 'inpayment',]
    form_excluded_columns = ['history', 'inpayment']
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
                         lastName='Last Name',
                         imageName='User Image')

    def is_accessible(self):
        return loginflask.current_user.is_authenticated


class MyItemModelView(ModelView):
    can_export = True
    export_types = ['csv']
    form_excluded_columns = 'items'

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
    # can_delete = False
    column_exclude_list = ['password', ]

    form_excluded_columns = 'password'

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

    # This callback executes when the User saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, changed_form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):
            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = model.password2
            # model.password = utils.encrypt_password(model.password2)

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
        # return redirect(url_for('bill.index'))

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle User login
        login_form = LoginForm(request.form)
        if helpers.validate_form_on_submit(login_form):
            user = login_form.get_user()
            loginflask.login_user(user)

        if loginflask.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = login_form
        #        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        loginflask.logout_user()
        return redirect(url_for('.index'))

class SnackBarIndexView(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('initial'))

init_login()
admin = Admin(app, name='SnackBar Admin Page', index_view=MyAdminIndexView(), base_template='my_master.html', template_mode='bootstrap2')
admin.add_view(MyBillView(name='Bill', endpoint='bill'))
# admin.add_view(MyAccountingView(name='Accounting', endpoint='accounting'))
admin.add_view(MyPaymentModelView(Inpayment, db.session, 'Inpayment'))
admin.add_view(MyUserModelView(User, db.session, 'User'))
admin.add_view(MyItemModelView(Item, db.session, 'Items'))
admin.add_view(MyHistoryModelView(History, db.session, 'History'))
admin.add_view(MyAdminModelView(Coffeeadmin, db.session, 'Admins'))
admin.add_view(MySettingsModelView(Settings, db.session, 'Settings'))
admin.add_view(SnackBarIndexView(name='Back to Snack Bar', endpoint='back'))

#admin.add_link(MenuLink(name='Snack Bar', url=url_for('initial')))

current_sorting = ""


@app.route('/')
def initial():
    global current_sorting
    initusers = get_users_with_leaders()
    users = sorted(initusers, key=lambda k: k['firstName'])

    if current_sorting == "za":
        users.reverse()
    elif current_sorting == "coffee19":
        users = sorted(users, key=lambda k: k['coffeeMonth'])
    elif current_sorting == "coffee91":
        users.reverse()
        users = sorted(users, key=lambda k: k['coffeeMonth'])
        users.reverse()

    else:
        current_sorting = "az"

    # if current_sorting == "az":
    #     users = sorted(initusers, key=lambda k: k['firstName'])
    # elif current_sorting == "za":
    #     users = sorted(initusers, key=lambda k: k['firstName'])
    #     users.reverse()
    # elif current_sorting == "coffee19":
    #     users = sorted(initusers, key=lambda k: k['coffeeMonth'])
    # elif current_sorting == "coffee91":
    #     users = sorted(initusers, key=lambda k: k['coffeeMonth'])
    #     users.reverse()
    # else:
    #     current_sorting = "az"
    #     users = sorted(initusers, key=lambda k: k['firstName'])

    return render_template('index.html', users=users, current_sorting=current_sorting)




@app.route('/sort/<sorting>')
def sort(sorting):
    global current_sorting
    current_sorting = sorting
    return redirect(url_for('initial'))


@app.route('/adduser', methods=('GET', 'POST'))
def adduser():
    if request.method == 'POST':
        first_name_error = False
        first_name = ''
        if request.form['firstname'] is None or request.form['firstname'] == '':
            first_name_error = true
        else:
            first_name = request.form['firstname']

        last_name_error = False
        last_name = ''
        if request.form['lastname'] is None or request.form['lastname'] == '':
            last_name_error = true
        else:
            last_name = request.form['lastname']

        from email.utils import parseaddr
        email_error = False
        email = ''
        if request.form['email'] is None or request.form['email'] == '':
            email_error = true
        else:
            email = parseaddr(request.form['email'])[1]
            if email == '':
                email_error = true

        if not first_name_error and not last_name_error and not email_error:
            with app.app_context():
                filename = ''
                if 'image' in request.files:
                    file = request.files['image']
                    imagename = first_name + "_" + file.filename  + "_ " + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
                    if imagename != '':# and allowed_file(imagename):
                        filename = secure_filename(imagename)
                        full_path = os.path.join(app.config['IMAGE_FOLDER'], filename)
                        file.save(full_path)

                new_user = User(firstname=first_name, lastname=last_name, email=email, imagename=filename)

                db.session.add(new_user)
                db.session.commit()
                send_email_new_user(new_user)

                return redirect(url_for('initial'))
        else:
            return render_template('adduser.html', firstNameError=first_name_error, firstName=first_name,
                                   lastNameError=last_name_error, lastName=last_name,
                                   emailError=email_error, email=email)
    else:
        return render_template('adduser.html', firstNameError=False, firstName='', lastNameError=False, lastName='',
                               emailError=False, email='')


def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/image/')
def default_image():
    userID = request.args.get('userID')
    return monster_image(None, userID)


@app.route('/image/<filename>')
def image(filename):
    userID = request.args.get('userID')
    return monster_image(filename, userID)


@app.route('/icon/')
def default_icon():
    return get_icon(None)


@app.route('/icon/<icon>')
def get_icon(icon):
    return image_from_folder(icon, app.config['ICON_FOLDER'], "static/unknown_icon.svg")


def monster_image(filename, userID):
    if filename is None:
        return monster_image_for_id(userID)

    fullpath = os.path.join(current_app.root_path, app.config['IMAGE_FOLDER'])

    full_file_path = safe_join(fullpath, filename)
    if not os.path.isabs(full_file_path):
        full_file_path = os.path.join(current_app.root_path, full_file_path)
    try:
        if not os.path.isfile(full_file_path):
            return  monster_image_for_id(userID)
        if os.stat(full_file_path).st_size < 1:
            return monster_image_for_id(userID)
    except (TypeError, ValueError):
        pass

    return send_from_directory(directory=fullpath, path=filename, as_attachment=False)



def monster_image_for_id(userID):
    if userID is None:
        userID = "example@example.org"

    use_gravatar = True
    returnValue = send_from_directory(directory=current_app.root_path, path="static/unknown_image.png",
                                      as_attachment=False)

    # mail_parts = userID.split("@")
    # if len(mail_parts) == 2:
    #     prefix = mail_parts[0]
    #     domain = mail_parts[1]
    #     if domain == "fit.fraunhofer.de":
    #         use_gravatar = False
    #         requestURL = "https://chat.fit.fraunhofer.de/avatar/" + prefix
    #         try:
    #             proxyResponse = requests.get(requestURL, timeout=5)
    #
    #             returnValue = Response(proxyResponse)
    #         except:
    #             pass

    if use_gravatar:
        userHash = hashlib.md5(str(userID).encode('utf-8').lower()).hexdigest()
        if userHash in imageCache:
            return imageCache[userHash]

        image = get_monster_id_from_gravatar(userHash)
        if image is False:
            image = get_wavatar_from_gravatar(userHash)

        if image is not False:
            returnValue = image
            imageCache[userHash] = returnValue
    return returnValue


def get_wavatar_from_gravatar(userHash):
    returnValue = False

    requestURL = "https://www.gravatar.com/avatar/" + userHash + "?s=100" + "&d=wavatar"
    try:
        proxyResponse = requests.get(requestURL, timeout=5)
        # imageCache[userHash] = returnValue
        statusCode = proxyResponse.status_code
        if statusCode == 200:
            returnValue = Response(proxyResponse)
    except:
        pass

    return returnValue

def get_monster_id_from_gravatar(userHash):

    returnValue = False

    requestURL = "https://www.gravatar.com/avatar/" + userHash + "?s=100" + "&d=monsterid"
    try:
        proxyResponse = requests.get(requestURL, timeout=5)
        # imageCache[userHash] = returnValue
        statusCode = proxyResponse.status_code
        if statusCode == 200:
            returnValue = Response(proxyResponse)
    except:
        pass

    return returnValue



def image_from_folder(filename, image_folder, the_default_image):
    if filename is None:
        return send_from_directory(directory=current_app.root_path, path=the_default_image, as_attachment=False)

    fullpath = os.path.join(current_app.root_path, image_folder)

    full_file_path = safe_join(fullpath, filename)
    if not os.path.isabs(full_file_path):
        full_file_path = os.path.join(current_app.root_path, full_file_path)
    try:
        if not os.path.isfile(full_file_path):
            return send_from_directory(directory=current_app.root_path, path=the_default_image, as_attachment=False)
    except (TypeError, ValueError):
        pass

    return send_from_directory(directory=fullpath, path=filename, as_attachment=False)
    # return redirect(url)


# from https://gist.github.com/deontologician/3503910
def reltime(date, compare_to=None, at='@'):
    """Takes a datetime and returns a relative representation of the
    time.
    :param date: The date to render relatively
    :param compare_to: what to compare the date to. Defaults to datetime.now()
    :param at: date/time separator. defaults to "@". "at" is also reasonable.
    """

    def ordinal(n):
        r"""Returns a string ordinal representation of a number
        Taken from: http://stackoverflow.com/a/739301/180718
        """
        if 10 <= n % 100 < 20:
            return str(n) + 'th'
        else:
            return str(n) + {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, "th")

    compare_to = compare_to or datetime.now()
    if date > compare_to:
        return NotImplementedError(f"reltime only handles dates in the past: {date} > {compare_to}")
    # get timediff values
    diff = compare_to - date
    if diff.seconds < 60 * 60 * 8:  # less than a business day?
        days_ago = diff.days
    else:
        days_ago = diff.days + 1
    months_ago = compare_to.month - date.month
    years_ago = compare_to.year - date.year
    weeks_ago = int(math.ceil(days_ago / 7.0))
    # get a non-zero padded 24-hour hour
    hr = date.strftime('%H')
    if hr.startswith('0'):
        hr = hr[1:]
    wd = compare_to.weekday()
    # calculate the time string
    _time = '{0}:{1}'.format(hr, date.strftime('%M').lower())

    # calculate the date string
    if days_ago == 0:
        datestr = 'today {at} {time}'
    elif days_ago == 1:
        datestr = 'yesterday {at} {time}'
    elif (wd in (5, 6) and days_ago in (wd + 1, wd + 2)) or \
            wd + 3 <= days_ago <= wd + 8:
        # this was determined by making a table of wd versus days_ago and
        # divining a relationship based on everyday speech. This is somewhat
        # subjective I guess!
        datestr = 'last {weekday} {at} {time} ({days_ago} days ago)'
    elif days_ago <= wd + 2:
        datestr = '{weekday} {at} {time} ({days_ago} days ago)'
    elif years_ago == 1:
        datestr = '{month} {day}, {year} {at} {time} (last year)'
    elif years_ago > 1:
        datestr = '{month} {day}, {year} {at} {time} ({years_ago} years ago)'
    elif months_ago == 1:
        datestr = '{month} {day} {at} {time} (last month)'
    elif months_ago > 1:
        datestr = '{month} {day} {at} {time} ({months_ago} months ago)'
    else:
        # not last week, but not last month either
        datestr = '{month} {day} {at} {time} ({days_ago} days ago)'
    return datestr.format(time=_time,
                          weekday=date.strftime('%A'),
                          day=ordinal(date.day),
                          days=diff.days,
                          days_ago=days_ago,
                          month=date.strftime('%B'),
                          years_ago=years_ago,
                          months_ago=months_ago,
                          weeks_ago=weeks_ago,
                          year=date.year,
                          at=at)


@app.route('/user/<int:userid>', methods=['GET'])
def user_page(userid):
    curuser = db.session.get(User, userid)
    if curuser is None:
        return redirect(url_for('initial'))
    user_name = '{} {}'.format(curuser.firstName, curuser.lastName)
    items = list()
    leader_data = get_all_leader_data()

    for instance in Item.query:
        rank_info = get_rank(userid, instance.itemid, leader_data)
        items.append({'name': '{}'.format(instance.name),
                      'price': instance.price,
                      'itemid': '{}'.format(instance.itemid),
                      'icon': '{}'.format(instance.icon),
                      'count': get_unpaid(userid, instance.itemid, leader_data),
                      'total': get_total(userid, instance.itemid),
                      'rank': rank_info['rank'],
                      'ub': rank_info['upperbound'],
                      'lb': rank_info['lowerbound']})

    no_users = User.query.filter(User.hidden.is_(False)).count()
    currbill = rest_bill(userid)
    can_change_image = settings_for('usersCanChangeImage')

    last_purchase = "-"
    last_purchase_item = History.query.filter(History.userid == userid).order_by(History.date.desc()).first()
    if last_purchase_item is not None:
        # last_purchase = last_purchase_item.date.strftime('%Y-%m-%d %H:%M')
        last_purchase = reltime(last_purchase_item.date)

    return render_template('choices.html',
                           currbill=currbill,
                           chosenuser=user_name,
                           userid=userid,
                           items=items,
                           noOfUsers=no_users,
                           canChangeImage=can_change_image,
                           last_purchase=last_purchase
                           )


def send_email_new_user(curuser):
    if curuser.email:
        mymail = Bimail('SnackBar User Created', ['{}'.format(curuser.email)])
        mymail.sendername = settings_for('mailSender')
        mymail.sender = settings_for('mailSender')
        mymail.servername = settings_for('mailServer')
        # start html body. Here we add a greeting.
        mymail.htmladd(
            'Hallo {} {},<br><br>ein neuer Benutzer wurde mit dieser E-Mail Adresse erstellt. Solltest du diesen '
            'Acocunt nicht erstellt habe, melde dich bitte bei {}.<br><br>Ciao,<br>SnackBar Team [{}]'
            '<br><br><br><br>---------<br><br><br><br>'
            'Hello {} {},<br><br>a new User has been created with this mail address. If you have not created this '
            'Acocunt, please contact {}.<br><br>Ciao,<br>SnackBar Team [{}]'.format(
                curuser.firstName, curuser.lastName, settings_for('snackAdmin'), settings_for('snackAdmin'),
                curuser.firstName,
                curuser.lastName, settings_for('snackAdmin'), settings_for('snackAdmin')))
        # Further things added to body are separated by a paragraph, so you do not need to worry about
        # newlines for new sentences here we add a line of text and an html table previously stored
        # in the variable
        # add image chart title
        # attach another file
        # mymail.htmladd('Ciao,<br>SnackBar Team [Clemens Putschli (C5-315)]')
        # mymail.addattach([os.path.join(fullpath, filename)])
        # send!
        # print(mymail.htmlbody)
        mymail.send()


def send_reminder(curuser):
    if curuser.email:
        curn_bill_float = rest_bill(curuser.userid)
        minimum_balance = float(settings_for('minimumBalance'))
        if curn_bill_float <= minimum_balance:
            currbill = '{0:.2f}'.format(rest_bill(curuser.userid))
            # print(instance.firstName)
            # print(currbill)
            mymail = Bimail('SnackBar Reminder', ['{}'.format(curuser.email)])
            mymail.sendername = settings_for('mailSender')
            mymail.sender = settings_for('mailSender')
            mymail.servername = settings_for('mailServer')
            # start html body. Here we add a greeting.
            mymail.htmladd(
                'Hallo {} {},<br><br>du hast nur noch wenig Geld auf deinem SnackBar Konto ({} €). '
                'Zahle bitte ein bisschen Geld ein, damit wir wieder neue Snacks kaufen können!'
                '<br><br>Ciao,<br>SnackBar Team [{}]<br><br><br><br>---------<br><br><br><br>'
                'Hello {} {},<br><br>your SnackBar balance is very low ({} €). '
                'Please top it up with some money!<br><br>Ciao,<br>SnackBar Team [{}]'.format(
                    curuser.firstName, curuser.lastName, currbill, settings_for('snackAdmin'), curuser.firstName,
                    curuser.lastName, currbill, settings_for('snackAdmin')))
            # Further things added to body are separated by a paragraph, so you do not need to
            # worry about newlines for new sentences here we add a line of text and an html table
            # previously stored in the variable
            # add image chart title
            # attach another file
            # mymail.htmladd('Ciao,<br>SnackBar Team [Clemens Putschli (C5-315)]')
            # mymail.addattach([os.path.join(fullpath, filename)])
            # send!
            # print(mymail.htmlbody)
            mymail.send()

def create_bill():
    with app.app_context():
        initusers = list()
        total_bill = 0
        total_cash = db.session.query(func.sum(Inpayment.amount)).scalar()

        for instance in User.query.filter(User.hidden.is_(False)):
            bill = rest_bill(instance.userid)
            total_bill += bill
            initusers.append({'name': '{} {}'.format(instance.firstName, instance.lastName),
                                'userid': '{}'.format(instance.userid),
                                'bill': bill})

        users = sorted(initusers, key=lambda k: k['name'])

        bill_date = datetime.now()

        return total_cash, total_bill, users, bill_date


def save_bill(total_cash, total_bill, bill_date):
    #filename = 'CoffeeBill_{}_{}.csv'.format(bill_date.date().isoformat(),bill_date.time().strftime('%H-%M-%S'))
    filename = 'CoffeeBill.csv'
    
    # export_path
    root_path = os.path.dirname(os.path.abspath(__file__))
    export_path = os.path.join(root_path, "bill")
    if not os.path.exists(export_path):
        os.makedirs(export_path)

    full_export_path = os.path.join(export_path, filename)

    # check if export file already exists (if not then create it and add header)
    if not os.path.exists(full_export_path):
        # create file
        with open(full_export_path, "w") as file:
            writer = csv.writer(file)
            # Daten an die CSV-Datei anhängen
            writer.writerow(["Date", "Total Cash", "Total Open Bill", "Resulting Sum"])

    today = bill_date.strftime('%Y-%m-%d %H-%M-%S')
    #Append to CSV file
    with open(full_export_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        
        # Daten an die CSV-Datei anhängen
        writer.writerow([today, "{:0.2f}".format(total_cash), "{:0.2f}".format(total_bill), "{:0.2f}".format((total_cash - total_bill))])
	
	
def send_bill_to(user, total_cash, total_bill, users, bill_date):
    if user.email:

        today = bill_date.strftime('%Y-%m-%d')

        header = "Bill SnackBar: {}".format(today)

        toptable = """
            <table>
            <thead><tr><th colspan="2">Total</th></tr></thead>
            <tbody>
            <tr><td>Total Cash: </td><td>{:0.2f} €</td></tr>
            <tr><td>Total Open Bill: </td><td>{:0.2f} €</td></tr>
            <tr><td><b>Resulting Sum: </b></td><td><b>{:0.2f} €</b></td></tr>
            </tbody>
            </table><br/>
            """.format(total_cash, total_bill, (total_cash - total_bill))

        bottomtable = """
            <table>
            <thead><tr><th>Name</th><th>Bill</th></tr></thead>
            <tbody>
            """
        for aUser in users:
            bottomtable = bottomtable + "<tr><td>{}</td><td>{:0.2f} €</td></tr>".format(aUser['name'], aUser['bill'])

        bottomtable = bottomtable + """
            <tr></tr>
            <tr><td><b>SUM:</b></td><td><b>{:0.2f} €</b></td></tr>
            </tbody>
            </table><br/>
        """.format(total_bill)


        # print(instance.firstName)
        # print(currbill)
        mymail = Bimail(header, ['{}'.format(user.email)])
        mymail.sendername = settings_for('mailSender')
        mymail.sender = settings_for('mailSender')
        mymail.servername = settings_for('mailServer')
        # start html body. Here we add a greeting.
        mymail.htmladd("""
        <b>{}</b>
        <br/><br/>
        {}
        {}
        """.format(header, toptable, bottomtable))

        # Further things added to body are separated by a paragraph, so you do not need to
        # worry about newlines for new sentences here we add a line of text and an html table
        # previously stored in the variable
        # add image chart title
        # attach another file
        # mymail.htmladd('Ciao,<br>SnackBar Team [Clemens Putschli (C5-315)]')
        # mymail.addattach([os.path.join(fullpath, filename)])
        # send!
        # print(mymail.htmlbody)
        mymail.send()



def send_email(curuser, curitem):
    if curuser.email:
        if settings_for('instantMail') == 'true':
            currbill = '{0:.2f}'.format(rest_bill(curuser.userid))
            # print(instance.firstName)
            # print(currbill)
            mymail = Bimail('SnackBar++ ({} {})'.format(curuser.firstName, curuser.lastName), ['{}'.format(curuser.email)])
            mymail.sendername = settings_for('mailSender')
            mymail.sender = settings_for('mailSender')
            mymail.servername = settings_for('mailServer')
            # start html body. Here we add a greeting.

            today = datetime.now().strftime('%Y-%m-%d %H:%M')
            mymail.htmladd(
                'Hallo {} {}, <br>SnackBar hat gerade "{}" ({} €) für dich GEBUCHT! '
				'<br><br> Dein Guthaben beträgt jetzt {} € <br><br>'.format(
                    curuser.firstName, curuser.lastName, curitem.name, curitem.price, currbill))
            mymail.htmladd('Ciao,<br>SnackBar Team [{}]'.format(settings_for('snackAdmin')))
            mymail.htmladd('<br><br>---------<br><br>')
            mymail.htmladd(
                'Hello {} {}, <br>SnackBar has just ORDERED {} ({} €) for you! '
                '<br><br> Your balance is now {} € <br><br> '.format(
                    curuser.firstName, curuser.lastName, curitem.name, curitem.price, currbill))
            # Further things added to body are separated by a paragraph, so you do not need to worry
            # about newlines for new sentences here we add a line of text and an html table previously
            # stored in the variable
            # add image chart title
            # attach another file
            mymail.htmladd('Ciao,<br>SnackBar Team [{}]'.format(settings_for('snackAdmin')))

            mymail.htmladd('<br><br>---------<br>Registered at: {}'.format(today))

            # mymail.addattach([os.path.join(fullpath, filename)])
            # send!
            # print(mymail.htmlbody)
            mymail.send()

def send_webhook(coffeeDict):
    webhook_thread = threading.Thread(target=send_webhook_now, args=(coffeeDict, ))
    webhook_thread.start()


def get_coffee_dict(curuser, curitem, base_url="", extra_data={}):
    leader_data = get_all_leader_data()

    curn_bill_float = rest_bill(curuser.userid)
    minimum_balance = float(settings_for('minimumBalance'))
    if curn_bill_float <= minimum_balance:
        shouldTopUpMoney = True
    else:
        shouldTopUpMoney = False

    coffeeDict = {}

    coffeeDict["firstName"] = curuser.firstName
    coffeeDict["lastName"] = curuser.lastName
    coffeeDict["userId"] = curuser.userid
    coffeeDict["name"] = '{} {}'.format(curuser.firstName, curuser.lastName)
    coffeeDict["item"] = curitem.name
    coffeeDict["itemId"] = curitem.itemid
    coffeeDict["price"] = curitem.price
    coffeeDict["monthlyCount"] = get_unpaid(curuser.userid, curitem.itemid, leader_data)
    coffeeDict["total"] = get_total(curuser.userid, curitem.itemid)
    coffeeDict["shouldTopUpMoney"] = shouldTopUpMoney
    coffeeDict["userPage"] = urllib.parse.urljoin(base_url, url_for('user_page', userid=curuser.userid))
    coffeeDict["extra_data"] = extra_data
    return coffeeDict

def send_webhook_now(coffeeDict):
    if settings_for('publishToMqtt') == 'true' and settings_for('mqttTopic') != '' and settings_for('mqttServer') != '' and settings_for('mqttPort') != '':
        data_out = json.dumps(coffeeDict)

        broker_url = settings_for('mqttServer')
        broker_port = int(settings_for('mqttPort'))
        broker_topic = settings_for('mqttTopic')

        mqtt_publish.single(broker_topic, payload=data_out,hostname=broker_url, port=broker_port)



@app.post('/api/buy')
def api_buy():
    # docker überprüfen
    # und deployen
    try:
        try:
            # Get the JSON data from the request
            data = request.get_json(force=True)
        except Exception as e:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": f"Content-Type not supported! Please use the JSON format.",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        userId = data.get('userId')
        userName = data.get('userName')
        if userId is not None:
            curuser = db.session.get(User, userId)
        elif userName is not None:
            name_array =  userName.rsplit(" ", 1)
            if len(name_array) == 1 :
                firstName = ""
                lastName = name_array[0]
            elif len(name_array) == 2 :
                firstName = name_array[0]
                lastName = name_array[1]
            else:
                raise Exception
            curuser = db.session.query(User).filter_by(firstName=firstName, lastName=lastName).first()
            if curuser is None:
                with app.app_context():
                    curuser = User(firstname=firstName, lastname=lastName, email='', imagename='')
                    db.session.add(curuser)
                    db.session.commit()
                    #send_email_new_user(new_user)

        else:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "No userID or userName provided. Example Json: {\"userId\": someUserId, \"itemId\": someItemId } or {\"userName\": \"Firstname Lastname\", \"itemId\": someItemId }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        if curuser is None:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "Could not find User. The userId is probably wrong. Example Json: {\"userId\": someUserId, \"itemId\": someItemId } or {\"userName\": \"Firstname Lastname\", \"itemId\": someItemId }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        itemId = data.get('itemId')
        if itemId is None:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "No itemId provided. Example Json: {\"userId\": someUserId, \"itemId\": someItemId } or {\"userName\": \"Firstname Lastname\", \"itemId\": someItemId }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        curitem = db.session.get(Item, itemId)
        if curitem is None:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "Could not find Item. The itemId is probably wrong. Example Json: {\"userId\": someUserId, \"itemId\": someItemId } or {\"userName\": \"Firstname Lastname\", \"itemId\": someItemId }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        user_purchase = History(curuser, curitem, curitem.price)

        db.session.add(user_purchase)
        db.session.commit()

        send_email(curuser, curitem)
        base_url = request.base_url.replace( url_for('api_buy'), "")
        coffeeDict = get_coffee_dict(curuser, curitem, base_url, get_extra_data(request))
        try:
            send_webhook(coffeeDict)
        except:
            pass

        response = Response(json.dumps(
            {"data": coffeeDict, "message": "", "status": "ok"}), mimetype='application/json')
        response.status_code = 200
        return response


    except Exception as e:
        response = Response(json.dumps(
            {"data": "",
             "status": "error",
             "message": f"Some unknown error occured: Exception: {''.join(traceback.format_exception(e))}",
            }), mimetype='application/json')
        response.status_code = 400
        return response




def get_extra_data(theRequest):
    return_data = {}
    if theRequest.environ.get('HTTP_X_FORWARDED_FOR') is not None:
        return_data["remote_address"] = theRequest.environ['HTTP_X_FORWARDED_FOR']
    elif theRequest.environ.get('REMOTE_ADDR') is not None:
        return_data["remote_address"] = theRequest.environ['REMOTE_ADDR']
    elif theRequest.remote_addr is not None:
        return_data["remote_address"] = theRequest.remote_addr

    if theRequest.referrer is not None:
        return_data["referrer"] = theRequest.referrer

    if theRequest.user_agent is not None:
        return_data["user_agent"] = theRequest.user_agent.string


    return return_data


@app.route('/analysis')
def analysis():
    content, tags_hours_labels = get_analysis()
    return render_template('analysis.html', content=content, tagsHoursLabels=tags_hours_labels)

@app.route('/analysis/slide')
def analysis_slide():
    content, tags_hours_labels = get_analysis()
    return render_template('analysisSlide.html', content=content, tagsHoursLabels=tags_hours_labels)


def get_analysis():
    with app.app_context():
        # get no of users

        # noUsers = db.session.query(User).count()
        # print('Number of users is: {}'.format(noUsers))
        content = dict()

        tags_hours = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00',
                      '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00',
                      '22:00', '23:00']
        min_tag = len(tags_hours)
        max_tag = 0

        all_items = Item.query.filter(Item.name is not None, Item.name != '')
        all_item_id = [int(instance.itemid) for instance in all_items]

        # Info for Coffee
        for itemID in all_item_id:
            histogram = db.session.query(History.itemid, History.date, History.userid). \
                filter(History.itemid == itemID).all()

            # Info Item on weekhours
            histogram_hours = list()
            for x in histogram:
                if x[1] is not None:
                    histogram_hours.append(x[1].time().replace(minute=0, second=0, microsecond=0))

            bla = list(sorted(Counter(histogram_hours).items()))
            time_stamp = [x[0].strftime('%H:%M') for x in bla]

            for j, elem in enumerate(time_stamp):
                index = tags_hours.index(elem)
                min_tag = min(min_tag, index)
                max_tag = max(max_tag, index)

        min_tag = max(min_tag - 1, 0)
        max_tag = min(max_tag + 2, len(tags_hours))

        min_tag = min(min_tag, 9)
        max_tag = max(max_tag, 17)

        if min_tag < max_tag:
            tags_hours = tags_hours[min_tag:max_tag]

        # Info for Coffe
        for itemID in all_item_id:
            # itemID = 4

            itemtmp = db.session.query(Item.name).filter(Item.itemid == itemID).one()
            item_name = itemtmp[0]

            content[item_name] = dict()
            histogram = db.session.query(History.itemid, History.date, History.userid). \
                filter(History.itemid == itemID).all()
            # print("Total number of consumed {} is : {}".format(itemName,len(histogram)))
            if len(histogram) > 1:
                oldest_date = histogram[0][1]
                newest_date = histogram[-1][1]
                histogram_delta = newest_date - oldest_date
                second_delta = histogram_delta.seconds
            else:
                second_delta = 3600.0
                histogram_delta = timedelta(hours=1)

            content[item_name]['total'] = len(histogram)

            # print(len(histogram))
            # Info Item on weekday

            histogram_days = list()
            for x in histogram:
                if x[1] is not None:
                    histogram_days.append(x[1].isoweekday())

            bla = list(sorted(Counter(histogram_days).items()))
            # noinspection PyUnusedLocal
            amount = [0 for x in range(7)]
            for elem in bla:
                amount[elem[0] - 1] = elem[1]


            hour_delta = second_delta / 3600
            day_delta = hour_delta / 24
            total_day_delta = day_delta + histogram_delta.days
            total_day_delta = max(total_day_delta, 1)
            week_delta = total_day_delta / 7

            # for i in range(len(amount)):
            #     amount[i] = amount[i] / week_delta

            # amount = [x[1] for x in bla]
            content[item_name]['tagsDays'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            content[item_name]['amountDays'] = amount

            time_stamp = [x[0] for x in bla]
            time_stamp = [x + 1 for x in range(7)]

            # Info Item on weekhours
            histogram_minutes = list()
            for x in histogram:
                if x[1] is not None:
                    histogram_minutes.append(x[1].replace(minute=30, second=0, microsecond=0, month=1, day=1, year=2000))

            histogram_minutes_sorted = list(sorted(Counter(histogram_minutes).items()))

            all_minute_coffee = list()
            hour_after = None

            for j, element in enumerate(histogram_minutes_sorted):
                time_stamp = element[0]
                before = time_stamp.replace(minute=0, second=0, microsecond=0, month=1, day=1, year=2000)
                after = time_stamp.replace(minute=0, second=0, microsecond=0, month=1, day=1, year=2000)
                after = after + timedelta(hours=1)

                if before != hour_after and hour_after is not None:
                    all_minute_coffee.append((hour_after, 0))
                    all_minute_coffee.append((before, 0))

                if hour_after is None:
                    all_minute_coffee.append((before, 0))

                hour_after = after
                all_minute_coffee.append((time_stamp, element[1]))

            if hour_after is not None:
                all_minute_coffee.append((hour_after, 0))

            amount_points = []
            for j, element in enumerate(all_minute_coffee):
                time_stamp = element[0]
                time_string = time_stamp.strftime('%H:%M')
                amount_points.append({'y': element[1], 'x': time_string})

            # print(amountPoints)
            # print(amountRaw)

            # for i in range(len(amount_points)):
            #     amount_points[i]['y'] = amount_points[i]['y'] / total_day_delta

            content[item_name]['amountPoints'] = amount_points

            # Info Item on month

            histogram_month = list()
            for x in histogram:
                if x[1] is not None:
                    histogram_month.append(x[1].month)
            bla = list(sorted(Counter(histogram_month).items()))
            time_stamp = [x for x in range(12)]
            amount_month = [0 for x in range(12)]
            for elem in bla:
                amount_month[elem[0] - 1] = elem[1]

            month_delta = total_day_delta / 30
            # for i in range(len(amount_month)):
            #     amount_month[i] = amount_month[i] / month_delta

            content[item_name]['amountMonth'] = amount_month
            content[item_name]['tagsMonth'] = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov',
                                               'Dec']

        return content, tags_hours



@app.route('/change_image', methods=(['POST']))
def change_image():
    with app.app_context():
        if 'image' in request.files:
            file = request.files['image']
            imagename = file.filename
            userid = request.form["userid"]
            imagename = str(userid) + "_" + imagename + "_ " + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            if imagename != '': #  and allowed_file(imagename):
                userid = request.form["userid"]
                filename = secure_filename(imagename)
                full_path = os.path.join(app.config['IMAGE_FOLDER'], filename)
                add = 0
                while os.path.isfile(full_path):
                    add = add + 1
                    split = imagename.rsplit('.', 1)
                    part_1 = split[0] + "_" + str(add)
                    new_imagename = ".".join([part_1, split[1]])
                    filename = secure_filename(new_imagename)
                    full_path = os.path.join(app.config['IMAGE_FOLDER'], filename)

                file.save(full_path)


                current_user = db.session.get(User, userid)
                current_user.imageName = filename

                db.session.commit()

    return redirect(url_for('initial'))




def build_sample_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

        with open('userList.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                newuser = User(firstname='{}'.format(row['FirstName']),
                               lastname='{}'.format(row['LastName']),
                               imagename='{}'.format(row['ImageName']),
                               email='{}'.format(row['email']))
                db.session.add(newuser)
                initial_balance = '{}'.format(row['InitialBalance'])
                # noinspection PyBroadException,PyPep8
                try:
                    initial_balance_float = float(initial_balance)
                    if initial_balance_float != 0:
                        initial_payment = Inpayment(amount=initial_balance)
                        initial_payment.user = newuser
                        db.session.add(initial_payment)
                except:
                    pass

        '''
        name = [
            'Wilhelm Müller', 'Franz Meier', 'Berta Schmitt', 'Fritz Hase']
        email = [
            'wilhelm@mueller.de', 'franz@meier.de', 'berta@schmitt.de', 'fritz@hase.de']
    
        for i in range(len(name)):
            newuser = User(username='{}'.format(name[i]),email = '{}'.format(email[i]))
            #newuser.username = name[i]
            #newuser.email = email[i]
        '''

        itemname = ['Coffee', 'Water', 'Snacks', 'Cola']
        price = [0.2, 0.55, 0.2, 0.4]

        for i in range(len(itemname)):
            newitem = Item(name='{}'.format(itemname[i]), price=float('{}'.format(price[i])))
            newitem.icon = "item" + str(i + 1) + ".svg"
            # newitem.name = itemname[i]
            # newitem.price = price[i]
            db.session.add(newitem)

        newadmin = Coffeeadmin(name='admin', password='admin', send_bill=False, email='')
        db.session.add(newadmin)

        db.session.commit()
    return


def set_default_settings():
    with app.app_context():
        with open('defaultSettings.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = '{}'.format(row['key'])
                db_entry = db.session.query(Settings).filter_by(key=key).first()
                if db_entry is None:
                    newsettingitem = Settings(key='{}'.format(row['key']), value='{}'.format(row['value']))
                    db.session.add(newsettingitem)

        db.session.commit()


# noinspection PyBroadException,PyPep8
def send_reminder_to_all():
    with app.app_context():
        try:
            for aUser in User.query.filter(User.hidden.is_(False)):
                send_reminder(aUser)
        except:
            pass

def send_bill_to_admin():
    with app.app_context():
        total_cash, total_bill, users, bill_date = create_bill()
        save_bill(total_cash, total_bill, bill_date)

        try:
            for aAdmin in Coffeeadmin.query.filter(Coffeeadmin.send_bill.is_(True)):
                send_bill_to(aAdmin, total_cash, total_bill, users, bill_date)
        except:
            pass


def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":

    if not os.path.isfile(databaseName):
        build_sample_db()


    schedule.every().monday.at("10:30").do(send_reminder_to_all)
    schedule.every().monday.at("00:00").do(send_bill_to_admin)
    schedule_thread = threading.Thread(target=run_schedule).start()

    set_default_settings()
    # app.run()
    # app.run(host='0.0.0.0', port=5000, debug=False)


    # Email Errors to Admins
    mail_handler = SMTPHandler(
        mailhost=settings_for('mailServer'),
        fromaddr=settings_for('mailSender'),
        toaddrs=['clemens.eyhoff@fit.fraunhofer.de'],
        subject='Application Error'
    )
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    if not options.debug:
        app.logger.addHandler(mail_handler)

    flaskrun(app, options=options)
