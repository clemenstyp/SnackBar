import flask_login as loginflask
from flask_admin import BaseView, expose

from Snackbar.Helper.Database import get_total_bill


class MyAccountingView(BaseView):

    @expose('/')
    def index(self):
        accounting, total_cash, total_open = get_total_bill()

        return self.render('Adminpanel/accounting.html', data=reversed(accounting), total_cash=total_cash,
                           total_open=total_open, total_sum=(total_cash + total_open))

    def is_accessible(self):
        return loginflask.current_user.is_authenticated
