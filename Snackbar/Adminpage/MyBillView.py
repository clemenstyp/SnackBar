import flask_login as loginflask
from flask import redirect, url_for
from flask_admin import BaseView, expose
from sqlalchemy import func

from Snackbar import db
# from Snackbar.Helper.Database import make_xls_bill
from Snackbar.Helper.Mailing import send_reminder
from Snackbar.models import Inpayment, User


class MyBillView(BaseView):

    @expose('/')
    def index(self):

        initusers = list()
        total_bill = 0
        total_cash = db.session.query(func.sum(Inpayment.amount)).scalar()
        if total_cash is None:
            total_cash = 0

        for aUser in User.query.filter(User.hidden.is_(False)):
            bill = aUser.calculate_account_balance()
            total_bill += bill
            initusers.append({'name': '{} {}'.format(aUser.firstName, aUser.lastName),
                              'userid': '{}'.format(aUser.userid),
                              'bill': bill})

        users = sorted(initusers, key=lambda k: k['name'])

        init_hidden_users = list()
        hidden_total_bill = 0
        for aUser in User.query.filter(User.hidden.is_(True)):
            bill = aUser.calculate_account_balance()
            hidden_total_bill += bill
            init_hidden_users.append({'name': '{} {}'.format(aUser.firstName, aUser.lastName),
                                      'userid': '{}'.format(aUser.userid),
                                      'bill': bill})

        hidden_users = sorted(init_hidden_users, key=lambda k: k['bill'])

        return self.render('admin/bill.html', users=users, hidden_users=hidden_users,
                           hidden_total_bill=hidden_total_bill, total_bill=total_bill, total_cash=total_cash,
                           total_sum=(total_cash - total_bill))

    @expose('/reminder/')
    def reminder(self):
        for aUser in User.query.filter(User.hidden.is_(False)):
            send_reminder(aUser)
        return redirect(url_for('admin.index'))

    def is_accessible(self):
        return loginflask.current_user.is_authenticated
