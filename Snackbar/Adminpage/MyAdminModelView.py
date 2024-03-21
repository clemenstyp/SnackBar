import flask_login as loginflask
from flask import flash
from flask_admin.contrib.sqla import ModelView
from wtforms import fields


class MyAdminModelView(ModelView):
    can_export = False
    # can_delete = False
    column_exclude_list = ('password',)

    form_excluded_columns = 'password'

    def is_accessible(self):
        return loginflask.current_user.is_authenticated

    # On the form for creating or editing a User, don't display a field corresponding to the Models's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a regular text field.

    def scaffold_form(self):
        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(MyAdminModelView, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New Password".
        form_class.password2 = fields.PasswordField('New Password')

        return form_class

    # This callback executes when the User saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, changed_form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):
            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = model.password2
            # Models.password = utils.encrypt_password(Models.password2)

    def delete_model(self, model):
        if loginflask.current_user.id == model.id:
            flash('You cannot delete your own account.')
            return False
        else:
            return super(MyAdminModelView, self).delete_model(model)
