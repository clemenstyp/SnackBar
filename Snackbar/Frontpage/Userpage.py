import os
import random
import string

from flask import render_template, request, redirect, url_for
from markupsafe import Markup
from werkzeug.utils import secure_filename

from Snackbar import app
from Snackbar.Helper.Appearance import reltime
from Snackbar.Helper.Database import get_all_leader_data
from Snackbar.Helper.Database import settings_for, get_unpaid, get_total, get_rank
from Snackbar.Helper.Mailing import send_email_new_user
from Snackbar.models import History, Item, User, db


@app.route('/user/<int:userid>', methods=['GET'])
def user_page(userid):
    curuser = db.session.get(User, userid)
    if curuser is None:
        return redirect(url_for('initial'))
    user_name = '{} {}'.format(curuser.firstName, curuser.lastName)
    items = list()
    leader_data = get_all_leader_data()

    for instance in Item.query:
        rank_info = get_rank(userid, instance.itemid, leader_data)
        items.append({'name': '{}'.format(instance.name),
                      'price': instance.price,
                      'itemid': '{}'.format(instance.itemid),
                      'icon': '{}'.format(instance.icon),
                      'count': get_unpaid(userid, instance.itemid, leader_data),
                      'total': get_total(userid, instance.itemid),
                      'rank': rank_info['rank'],
                      'ub': rank_info['upperbound'],
                      'lb': rank_info['lowerbound']})

    no_users = User.query.filter(User.hidden.is_(False)).count()
    currbill = curuser.calculate_account_balance()
    can_change_image = settings_for('usersCanChangeImage')

    last_purchase = "-"
    last_purchase_item = History.query.filter(History.userid == userid).order_by(History.date.desc()).first()
    if last_purchase_item is not None:
        # last_purchase = last_purchase_item.date.strftime('%Y-%m-%d %H:%M')
        last_purchase = reltime(last_purchase_item.date)

    return render_template('choices.html',
                           currbill=currbill,
                           chosenuser=user_name,
                           userid=userid,
                           items=items,
                           noOfUsers=no_users,
                           canChangeImage=can_change_image,
                           last_purchase=last_purchase
                           )


@app.route('/adduser', methods=('GET', 'POST'))
def adduser():
    if request.method == 'POST':
        first_name_error = False
        first_name = ''
        if request.form['firstname'] is None or request.form['firstname'] == '':
            first_name_error = True
        else:
            first_name = request.form['firstname']

        last_name_error = False
        last_name = ''
        if request.form['lastname'] is None or request.form['lastname'] == '':
            last_name_error = True
        else:
            last_name = request.form['lastname']

        from email.utils import parseaddr
        email_error = False
        email = ''
        if request.form['email'] is None or request.form['email'] == '':
            email_error = True
        else:
            email = parseaddr(request.form['email'])[1]
            if email == '':
                email_error = True

        if not first_name_error and not last_name_error and not email_error:
            with app.app_context():
                filename = ''
                if 'image' in request.files:
                    file = request.files['image']
                    if file.filename != "":
                        imagename_extension = file.filename.rsplit('.', 1)[-1]
                        imagename = file.filename.rsplit('.',1)[0]
                        imagename = first_name + "_" + imagename + "_ " + ''.join(
                            random.choice(string.ascii_uppercase + string.digits) for _ in
                            range(6)) + '.' + imagename_extension
                        if imagename != '':  # and allowed_file(imagename):
                            filename = secure_filename(imagename)
                            full_path = os.path.join(app.config['IMAGE_FOLDER'], filename)
                            file.save(full_path)

                new_user = User(firstName=first_name, lastName=last_name, email=email, imageName=filename)

                db.session.add(new_user)
                db.session.commit()
                send_email_new_user(new_user)

                return redirect(url_for('initial'))
        else:
            return render_template('adduser.html', firstNameError=first_name_error, firstName=first_name,
                                   lastNameError=last_name_error, lastName=last_name,
                                   emailError=email_error, email=email)
    else:
        return render_template('adduser.html', firstNameError=False, firstName='', lastNameError=False, lastName='',
                               emailError=False, email='')


@app.template_filter("itemstrikes")
def itemstrikes(value):
    counter = 0
    tag_opened = False
    out = ""
    if value > 4:
        out = "<s>"
        tag_opened = True
    for f in range(value):
        counter += 1
        if counter % 5 == 0:
            out += "</s> "
            if value - counter > 4:
                out += "<s>"
        else:
            out += "|"
    if tag_opened:
        out += "</s>"
    out += " (%d)" % value
    return Markup(out)
