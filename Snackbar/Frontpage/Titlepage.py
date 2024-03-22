import os
import random
import string

from flask import render_template, request, redirect, url_for, make_response
from werkzeug.utils import secure_filename

from Snackbar import app, db
from Snackbar.Helper.Appearance import monster_image, image_from_folder
from Snackbar.Helper.Database import get_users_with_leaders
from Snackbar.models import User


@app.route('/')
def initial():
    sorting = request.args.get('sorting', default=None, type=str)
    if sorting is None:
        current_sorting = request.cookies.get('current_sorting')
    else:
        current_sorting = sorting
    initusers = get_users_with_leaders()
    users = sorted(initusers, key=lambda k: k['firstName'])

    if current_sorting == "za":
        users.reverse()
    elif current_sorting == "coffee19":
        users = sorted(users, key=lambda k: k['coffeeMonth'])
    elif current_sorting == "coffee91":
        users.reverse()
        users = sorted(users, key=lambda k: k['coffeeMonth'])
        users.reverse()
    else:
        current_sorting = "az"

    resp = make_response(render_template('index.html', users=users, current_sorting=current_sorting))
    resp.set_cookie('current_sorting', current_sorting)
    return resp
    # return render_template('index.html', users=users, current_sorting=sorting)



@app.route('/image/')
def default_image():
    userID = request.args.get('userID')
    return monster_image(None, userID)


@app.route('/image/<filename>')
def image(filename):
    userID = request.args.get('userID')
    return monster_image(filename, userID)


@app.route('/icon/')
def default_icon():
    return get_icon(None)


@app.route('/icon/<icon>')
def get_icon(icon):
    return image_from_folder(icon, app.config['ICON_FOLDER'], "static/unknown_icon.svg")


@app.route('/change_image', methods=(['POST']))
def change_image():
    with app.app_context():
        if 'image' in request.files:
            file = request.files['image']
            imagename = file.filename
            userid = request.form["userid"]
            imagename = str(userid) + "_" + imagename + "_ " + ''.join(
                random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            if imagename != '':  # and allowed_file(imagename):
                userid = request.form["userid"]
                filename = secure_filename(imagename)
                full_path = os.path.join(app.config['IMAGE_FOLDER'], filename)
                add = 0
                while os.path.isfile(full_path):
                    add = add + 1
                    split = imagename.rsplit('.', 1)
                    part_1 = split[0] + "_" + str(add)
                    new_imagename = ".".join([part_1, split[1]])
                    filename = secure_filename(new_imagename)
                    full_path = os.path.join(app.config['IMAGE_FOLDER'], filename)

                file.save(full_path)

                current_user = db.session.get(User, userid)
                current_user.imageName = filename

                db.session.commit()

    return redirect(url_for('initial'))
