import flask_login as loginflask
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import func

from Snackbar import app
from Snackbar.models import Inpayment


class MyPaymentModelView(ModelView):
    can_create = True
    can_delete = False
    can_edit = True
    can_export = True
    # form_excluded_columns = 'date'
    export_types = ['csv']
    column_descriptions = dict()
    column_labels = dict(user='Name')
    column_default_sort = ('date', True)
    column_filters = ('username_or_placeholder', 'amount', 'date')
    column_list = ('username_or_placeholder', 'amount', 'date', 'notes')
    column_labels = dict(username_or_placeholder='Name')
    form_excluded_columns = ('username_or_placeholder')
    column_sortable_list = ('username_or_placeholder', 'date')
    list_template = 'admin/custom_list.html'

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

    def page_sum(self, current_page):
        with app.app_context():
            # this should take into account any filters/search inplace
            # _query = self.session.query(Inpayment).limit(self.page_size).offset(current_page * self.page_size)
            # page_sum = sum([payment.amount for payment in _query])

            view_args = self._get_list_extra_args()
            # Map column index to column name
            sort_column = self._get_column_by_idx(view_args.sort)
            if sort_column is not None:
                sort_column = sort_column[0]

            # Get page size
            page_size = view_args.page_size or self.page_size
            count, data = self.get_list(current_page, sort_column, view_args.sort_desc,
                                        view_args.search, view_args.filters, page_size=page_size)

            page_sum = 0
            for payment in data:
                page_sum += payment.amount

            if page_sum is None:
                page_sum = 0
            return '{0:.2f}'.format(page_sum)

    def total_sum(self):
        with app.app_context():
            # this should take into account any filters/search inplace
            total_sum = self.session.query(func.sum(Inpayment.amount)).scalar()
            if total_sum is None:
                total_sum = 0
            return '{0:.2f}'.format(total_sum)

    def render(self, template, **kwargs):
        # we are only interested in the list page
        if template == 'admin/custom_list.html':
            # append a summary_data dictionary into kwargs
            _current_page = kwargs['page']
            kwargs['summary_data'] = [
                {'title': 'Page Total', 'amount': self.page_sum(_current_page)},
                {'title': 'Grand Total', 'amount': self.total_sum()},
            ]
            kwargs['summary_title'] = [{'title': ''}, {'title': 'Amount'}, ]
        return super(MyPaymentModelView, self).render(template, **kwargs)
