# coding: utf-8
import csv
import math
import os
import threading
import time
from datetime import datetime
from hashlib import md5
from math import sqrt

import flask_login as loginflask
import schedule
import tablib
from flask import Flask, redirect, url_for, render_template, request, send_from_directory, current_app, safe_join, flash
from flask_admin import Admin, expose, helpers, AdminIndexView, BaseView
from flask_admin.base import MenuLink
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from flask_sqlalchemy import SQLAlchemy
from jinja2 import Markup
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy.sql import func
# noinspection PyPackageRequirements
from werkzeug.utils import secure_filename
# noinspection PyPackageRequirements
from wtforms import form, fields, validators

from flaskrun import flaskrun
from sendEmail import Bimail

databaseName = 'CoffeeDB.db'
url = 'sqlite:///' + databaseName
engine = create_engine(url, connect_args={'check_same_thread': False}, poolclass=SingletonThreadPool)
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

if not os.path.exists(app.config['IMAGE_FOLDER']):
    os.makedirs(app.config['IMAGE_FOLDER'])


def settings_for(key):
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
    login = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

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
        return db.session.query(Coffeeadmin).filter_by(name=self.login.data).first()


# noinspection PyUnusedLocal
class RegistrationForm(form.Form):
    login = fields.StringField(validators=[validators.required()])
    email = fields.StringField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if db.session.query(Coffeeadmin).filter_by(name=self.login.data).count() > 0:
            raise validators.ValidationError('Duplicate username')


def init_login():
    login_manager = loginflask.LoginManager()
    login_manager.init_app(app)

    # Create User loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(Coffeeadmin).get(user_id)


def getcurrbill(userid):
    curr_bill_new = db.session.query(func.sum(History.price)). \
        filter(History.userid == userid).scalar()
    if curr_bill_new is None:
        curr_bill_new = 0

    # bill = History.query.filter(History.userid == userid).filter(History.paid == False)
    # currbill = 0

    # for entry in bill:
    #     currbill += entry.price

    return curr_bill_new


def get_users():
    get_users_with_leaders(false)


def get_users_with_leaders(with_leader):
    initusers = list()
    all_items = Item.query.filter(Item.icon is not None, Item.icon != '', Item.icon != ' ')
    all_items_id = [int(instance.itemid) for instance in all_items]
    itemid = all_items_id[0]

    for instance in User.query.filter(User.hidden is not True):
        initusers.append({'firstName': '{}'.format(instance.firstName),
                          'lastName': '{}'.format(instance.lastName),
                          'imageName': '{}'.format(instance.imageName),
                          'id': '{}'.format(instance.userid),
                          'bgcolor': '{}'.format(button_background(instance.firstName + ' ' + instance.lastName)),
                          'fontcolor': '{}'.format(button_font_color(instance.firstName + ' ' + instance.lastName)),
                          'coffeeMonth': get_unpaid(instance.userid, itemid),
                          'leader': get_leader_data(instance.userid, not with_leader),
                          })
    return initusers


def get_leader_data(userid, skip):
    leader_info = list()
    if not skip:
        all_items = Item.query.filter(Item.icon is not None, Item.icon != '', Item.icon != ' ')
        i = 0
        for aItem in all_items:
            leader_id = int(get_leader(aItem.itemid))
            if leader_id == userid:
                item_id = int(aItem.itemid)
                icon_file = str(aItem.icon)
                position = (-7 + (i * 34))
                leader_info.append({"item_id": item_id, "icon": icon_file, "position": position})
                i = i + 1
    return leader_info


def get_leader(itemid):
    tmp_query = db.session.query(User.userid, func.count(History.price)). \
        outerjoin(History, and_(User.userid == History.userid, History.itemid == itemid,
                                extract('month', History.date) == datetime.now().month,
                                extract('year', History.date) == datetime.now().year)). \
        group_by(User.userid). \
        order_by(func.count(History.price).desc()).first()

    return tmp_query[0]


def get_rank(userid, itemid):
    tmp_query = db.session.query(User.userid, func.count(History.price)). \
        outerjoin(History, and_(User.userid == History.userid, History.itemid == itemid,
                                extract('month', History.date) == datetime.now().month,
                                extract('year', History.date) == datetime.now().year)). \
        group_by(User.userid). \
        order_by(func.count(History.price).desc()).all()

    user_id = [x[0] for x in tmp_query]
    item_sum = [x[1] for x in tmp_query]

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


def get_unpaid(userid, itemid):
    n_unpaid = db.session.query(History). \
        filter(History.userid == userid). \
        filter(History.itemid == itemid). \
        filter(extract('month', History.date) == datetime.now().month). \
        filter(extract('year', History.date) == datetime.now().year) \
        .count()

    if n_unpaid is None:
        n_unpaid = 0

    return n_unpaid


def get_total(userid, itemid):
    n_unpaid = db.session.query(History). \
        filter(History.userid == userid). \
        filter(History.itemid == itemid).count()

    if n_unpaid is None:
        n_unpaid = 0

    return n_unpaid


def get_payment(userid):
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

    for instance in User.query.filter(User.hidden is not True):
        firstline = list()
        firstline.append('{} {}'.format(instance.firstName, instance.lastName))

        for record in Item.query:
            firstline.append('{}'.format(get_unpaid(instance.userid, record.itemid)))

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


class AnalyticsView(BaseView):

    @expose('/')
    def index(self):

        initusers = list()

        for instance in User.query.filter(User.hidden is not True):
            initusers.append({'name': '{} {}'.format(instance.firstName, instance.lastName),
                              'userid': '{}'.format(instance.userid),
                              'bill': rest_bill(instance.userid)})

        users = sorted(initusers, key=lambda k: k['name'])

        return self.render('admin/test.html', users=users)

    @expose('/reminder/')
    def reminder(self):
        for aUser in User.query.filter(User.hidden is not True):
            send_reminder(aUser)
        return redirect(url_for('admin.index'))

    @expose('/export/')
    def export(self):
        filename = 'CoffeeBill_{}_{}.xls'.format(datetime.now().date().isoformat(),
                                                 datetime.now().time().strftime('%H-%M-%S'))

        fullpath = os.path.join(current_app.root_path, app.config['STATIC_FOLDER'])
        make_xls_bill(filename, fullpath)

        return send_from_directory(directory=fullpath, filename=filename, as_attachment=True)

    def is_accessible(self):
        return loginflask.current_user.is_authenticated


class MyPaymentModelView(ModelView):
    can_create = True
    can_delete = False
    can_edit = False
    can_export = True
    form_excluded_columns = 'date'
    export_types = ['csv', 'xls']
    column_default_sort = ('date', True)
    column_filters = ('user', 'amount', 'date')
    list_template = 'admin/custom_list.html'

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def date_format(self, context, model, name):
        field = getattr(model, name)
        return field.strftime('%Y-%m-%d %H:%M')

    column_formatters = dict(date=date_format)

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

    def page_sum(self, current_page):
        # this should take into account any filters/search inplace
        _query = self.session.query(Inpayment).limit(self.page_size).offset(current_page * self.page_size)
        page_sum = sum([payment.amount for payment in _query])
        return '{0:.2f}'.format(page_sum)

    def total_sum(self):
        # this should take into account any filters/search inplace
        total_sum = self.session.query(func.sum(Inpayment.amount)).scalar()
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
    export_types = ['csv', 'xls']
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
    export_types = ['csv', 'xls']
    form_excluded_columns = ('History', 'Inpayment')
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
    export_types = ['csv', 'xls']
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


init_login()
admin = Admin(app, name='SnackBar Admin Page', index_view=MyAdminIndexView(), base_template='my_master.html')
admin.add_view(AnalyticsView(name='Bill', endpoint='bill'))
admin.add_view(MyPaymentModelView(Inpayment, db.session, 'Inpayment'))
admin.add_view(MyUserModelView(User, db.session, 'User'))
admin.add_view(MyItemModelView(Item, db.session, 'Items'))
admin.add_view(MyHistoryModelView(History, db.session, 'History'))
admin.add_view(MyAdminModelView(Coffeeadmin, db.session, 'Admins'))
admin.add_view(MySettingsModelView(Settings, db.session, 'Settings'))
admin.add_link(MenuLink(name='Snack Bar', url='/'))

current_sorting = ""


@app.route('/')
def initial():
    global current_sorting
    initusers = get_users_with_leaders(true)

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
                    if file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
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
    return image(None)


@app.route('/image/<filename>')
def image(filename):
    return image_from_folder(filename, app.config['IMAGE_FOLDER'], "static/unknown_image.png")


@app.route('/icon/')
def default_icon():
    return get_icon(None)


@app.route('/icon/<icon>')
def get_icon(icon):
    return image_from_folder(icon, app.config['ICON_FOLDER'], "static/unknown_icon.svg")


def image_from_folder(filename, image_folder, the_default_image):
    if filename is None:
        return send_from_directory(directory=current_app.root_path, filename=the_default_image, as_attachment=False)

    fullpath = os.path.join(current_app.root_path, image_folder)

    full_file_path = safe_join(fullpath, filename)
    if not os.path.isabs(full_file_path):
        full_file_path = os.path.join(current_app.root_path, full_file_path)
    try:
        if not os.path.isfile(full_file_path):
            return send_from_directory(directory=current_app.root_path, filename=the_default_image, as_attachment=False)
    except (TypeError, ValueError):
        pass

    return send_from_directory(directory=fullpath, filename=filename, as_attachment=False)
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
        return NotImplementedError('reltime only handles dates in the past')
    # get timediff values
    diff = compare_to - date
    if diff.seconds < 60 * 60 * 8:  # less than a business day?
        days_ago = diff.days
    else:
        days_ago = diff.days + 1
    months_ago = compare_to.month - date.month
    years_ago = compare_to.year - date.year
    weeks_ago = int(math.ceil(days_ago / 7.0))
    # get a non-zero padded 12-hour hour
    hr = date.strftime('%I')
    if hr.startswith('0'):
        hr = hr[1:]
    wd = compare_to.weekday()
    # calculate the time string
    if date.minute == 0:
        _time = '{0}{1}'.format(hr, date.strftime('%p').lower())
    else:
        _time = '{0}:{1}'.format(hr, date.strftime('%M%p').lower())
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
    user_name = '{} {}'.format(User.query.get(userid).firstName, User.query.get(userid).lastName)
    items = list()

    for instance in Item.query:
        rank_info = get_rank(userid, instance.itemid)
        items.append({'name': '{}'.format(instance.name),
                      'price': instance.price,
                      'itemid': '{}'.format(instance.itemid),
                      'icon': '{}'.format(instance.icon),
                      'count': get_unpaid(userid, instance.itemid),
                      'total': get_total(userid, instance.itemid),
                      'rank': rank_info['rank'],
                      'ub': rank_info['upperbound'],
                      'lb': rank_info['lowerbound']})

    no_users = User.query.filter(User.hidden is not True).count()
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


def send_email(curuser, curitem):
    if curuser.email:
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
            'Hello {} {}, <br>SnackBar has just REGISTERED an other {} ({} €) for you! '
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


@app.route('/change/<int:userid>')
def change(userid):
    itemid = request.args.get('itemid')
    curuser = User.query.get(userid)
    curitem = Item.query.get(itemid)
    user_purchase = History(curuser, curitem, curitem.price)

    db.session.add(user_purchase)
    db.session.commit()

    send_email(curuser, curitem)
    return redirect(url_for('user_page', userid=userid))


@app.route('/analysis')
def analysis():
    from analysisUtils import main
    content, tags_hours_labels = main()
    return render_template('analysis.html', content=content, tagsHoursLabels=tags_hours_labels)


@app.route('/change_image', methods=(['POST']))
def change_image():
    with app.app_context():
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                full_path = os.path.join(app.config['IMAGE_FOLDER'], filename)
                file.save(full_path)

                userid = request.form["userid"]
                current_user = User.query.get(userid)
                current_user.imageName = filename

                db.session.commit()

    return redirect(url_for('initial'))


def build_sample_db():
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
        newitem = Item(name='{}'.format(itemname[i]), price=int('{}'.format(price[i])))
        newitem.icon = "Item" + str(i + 1) + ".svg"
        # newitem.name = itemname[i]
        # newitem.price = price[i]
        db.session.add(newitem)

    newadmin = Coffeeadmin(name='admin', password='admin')
    db.session.add(newadmin)

    db.session.commit()
    return


def set_default_settings():
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
    try:
        for aUser in User.query.filter(User.hidden is not True):
            send_reminder(aUser)
    except:
        pass


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
    # app.run(host='0.0.0.0', port=5000, debug=False)
    flaskrun(app)
