import flask_login as loginflask
from flask_admin.contrib.sqla import ModelView


class MySettingsModelView(ModelView):
    can_create = False
    can_edit = True
    can_delete = False
    can_export = False
    column_editable_list = ('value',)

    column_labels = dict(key='Name', value='Value')
    form_excluded_columns = 'key'

    def is_accessible(self):
        return loginflask.current_user.is_authenticated
