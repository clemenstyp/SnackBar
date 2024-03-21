from flask import redirect, url_for
from flask_admin import BaseView, expose


class SnackBarIndexView(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('initial'))
