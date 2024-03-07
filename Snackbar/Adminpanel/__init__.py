import flask_login as loginflask
from flask_admin import Admin

from Snackbar import db
from Snackbar.Adminpanel.MyAdminIndexView import MyAdminIndexView
from Snackbar.Adminpanel.MyAdminModelView import MyAdminModelView
from Snackbar.Adminpanel.MyBillView import MyBillView
from Snackbar.Adminpanel.MyHistoryModelView import MyHistoryModelView
from Snackbar.Adminpanel.MyItemModelView import MyItemModelView
from Snackbar.Adminpanel.MyPaymentModelView import MyPaymentModelView
from Snackbar.Adminpanel.MySettingsModelView import MySettingsModelView
from Snackbar.Adminpanel.MyUserModelView import MyUserModelView
from Snackbar.Adminpanel.SnackBarIndexView import SnackBarIndexView
from Snackbar.Models.Coffeeadmin import Coffeeadmin
from Snackbar.Models.History import History
from Snackbar.Models.Inpayment import Inpayment
from Snackbar.Models.Item import Item
from Snackbar.Models.Settings import Settings
from Snackbar.Models.User import User


def setup_admin(app):
    init_login(app)
    admin = Admin(app, name='SnackBar Admin Page', index_view=MyAdminIndexView(), base_template='my_master.html',
                  template_mode='bootstrap2')
    admin.add_view(MyBillView(name='Bill', endpoint='bill'))
    # Adminpanel.add_view(MyAccountingView(name='Accounting', endpoint='accounting'))
    admin.add_view(MyPaymentModelView(Inpayment, db.session, 'Inpayment'))
    admin.add_view(MyUserModelView(User, db.session, 'User'))
    admin.add_view(MyItemModelView(Item, db.session, 'Items'))
    admin.add_view(MyHistoryModelView(History, db.session, 'History'))
    admin.add_view(MyAdminModelView(Coffeeadmin, db.session, 'Admins'))
    admin.add_view(MySettingsModelView(Settings, db.session, 'Settings'))
    admin.add_view(SnackBarIndexView(name='Back to Snack Bar', endpoint='back'))

    # Adminpanel.add_link(MenuLink(name='Snack Bar', url=url_for('initial')))


def init_login(app):
    login_manager = loginflask.LoginManager()
    login_manager.init_app(app)

    # Create User loader function
    @login_manager.user_loader
    def load_user(user_id):
        with app.app_context():
            return db.session.get(Coffeeadmin, user_id)
