import flask_login as loginflask
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import FileUploadField

from Snackbar import app


class MyUserModelView(ModelView):
    can_export = True
    export_types = ['csv']
    column_exclude_list = ['history', 'inpayment', ]
    form_excluded_columns = ['history', 'inpayment']
    can_set_page_size = True
    # column_descriptions = dict(
    #     firstName='Name of the corresponding person'
    # )

    can_edit = True
    # column_editable_list = ('imageName',)
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

    column_list = ('firstName', 'lastName', 'email', 'imageName', 'hidden')
    column_sortable_list = ('firstName', 'lastName', 'email', 'imageName', 'hidden')

    def is_accessible(self):
        return loginflask.current_user.is_authenticated
