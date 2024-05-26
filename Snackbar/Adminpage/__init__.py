import flask_login as loginflask
from flask_admin import Admin

#from Snackbar import db
from Snackbar.Adminpage.MyAdminIndexView import MyAdminIndexView
from Snackbar.Adminpage.MyAdminModelView import MyAdminModelView
from Snackbar.Adminpage.MyBillView import MyBillView
from Snackbar.Adminpage.MyHistoryModelView import MyHistoryModelView
from Snackbar.Adminpage.MyItemModelView import MyItemModelView
from Snackbar.Adminpage.MyPaymentModelView import MyPaymentModelView
from Snackbar.Adminpage.MySettingsModelView import MySettingsModelView
from Snackbar.Adminpage.MyUserModelView import MyUserModelView
from Snackbar.Adminpage.SnackBarIndexView import SnackBarIndexView
from Snackbar.models import Coffeeadmin, History, Inpayment, Item, Settings, User, db


def setup_admin(app):
    init_login(app)
    admin = Admin(app, name='SnackBar Admin Page',
                  url=app.config["APPLICATION_ROOT"],
                  index_view=MyAdminIndexView(),
                  base_template='my_master.html',
                  template_mode='bootstrap3')

    admin.add_view(MyBillView(name='Bill', endpoint='bill'))
    # admin.add_view(MyAccountingView(name='Accounting', endpoint='accounting'))
    admin.add_view(MyPaymentModelView(Inpayment, db.session, 'Inpayment'))
    admin.add_view(MyUserModelView(User, db.session, 'User'))
    admin.add_view(MyItemModelView(Item, db.session, 'Items'))
    admin.add_view(MyHistoryModelView(History, db.session, 'History'))
    admin.add_view(MyAdminModelView(Coffeeadmin, db.session, 'Admins'))
    admin.add_view(MySettingsModelView(Settings, db.session, 'Settings'))
    admin.add_view(SnackBarIndexView(name='Back to Snack Bar', endpoint='back'))

    # admin.add_link(MenuLink(name='Snack Bar', url=url_for('initial')))


def init_login(app):
    login_manager = loginflask.LoginManager()
    login_manager.init_app(app)

    # Create User loader function
    @login_manager.user_loader
    def load_user(user_id):
        with app.app_context():
            return db.session.get(Coffeeadmin, user_id)
