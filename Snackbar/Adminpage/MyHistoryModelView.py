from datetime import datetime

import flask_login as loginflask
from flask_admin.contrib.sqla import ModelView


class MyHistoryModelView(ModelView):
    can_create = True
    can_export = True
    can_delete = True
    can_edit = True
    export_types = ['csv']
    column_descriptions = dict()
    column_labels = dict(user='Name')
    column_default_sort = ('date', True)
    column_filters = ('user', 'item', 'price', 'date')
    column_list = ('user', 'item', 'price', 'date')
    column_sortable_list = ('user', 'date')
    form_args = dict(date=dict(default=datetime.now()), price=dict(default=0))
    can_set_page_size = True
    
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
