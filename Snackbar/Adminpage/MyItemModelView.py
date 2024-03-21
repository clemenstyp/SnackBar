import flask_login as loginflask
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import FileUploadField

from Snackbar import app


class MyItemModelView(ModelView):
    can_export = True
    export_types = ['csv']
    form_excluded_columns = 'history'
    can_set_page_size = True
    
    base_path = app.config['ICON_FOLDER']
    form_overrides = dict(icon=FileUploadField)
    form_args = {
        'icon': {
            'base_path': base_path
        }
    }

    column_list = ('name', 'price')
    column_sortable_list = ('name', 'price')

    def is_accessible(self):
        return loginflask.current_user.is_authenticated
