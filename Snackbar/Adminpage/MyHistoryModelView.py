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
    column_filters = ('username_or_placeholder', 'item_or_placeholder', 'price', 'date')
    column_list = ('username_or_placeholder', 'item_or_placeholder', 'price', 'date')
    column_sortable_list = ('username_or_placeholder', 'item_or_placeholder', 'date')
    column_labels = dict(username_or_placeholder='Name', item_or_placeholder='Item')
    form_columns = ('user', 'item', 'price', 'date')
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
