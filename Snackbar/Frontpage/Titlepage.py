import os
import random
import string

from flask import render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

from Snackbar import app, db
from Snackbar.Helper.Appearance import monster_image, image_from_folder
from Snackbar.Helper.Database import get_users_with_leaders
from Snackbar.Models.User import User

current_sorting = ""


class Titlepage():

    @app.route('/')
    def initial(self):
        global current_sorting
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

        # if current_sorting == "az":
        #     users = sorted(initusers, key=lambda k: k['firstName'])
        # elif current_sorting == "za":
        #     users = sorted(initusers, key=lambda k: k['firstName'])
        #     users.reverse()
        # elif current_sorting == "coffee19":
        #     users = sorted(initusers, key=lambda k: k['coffeeMonth'])
        # elif current_sorting == "coffee91":
        #     users = sorted(initusers, key=lambda k: k['coffeeMonth'])
        #     users.reverse()
        # else:
        #     current_sorting = "az"
        #     users = sorted(initusers, key=lambda k: k['firstName'])

        return render_template('index.html', users=users, current_sorting=current_sorting)

    @app.route('/sort/<sorting>')
    def sort(self, sorting):
        global current_sorting
        current_sorting = sorting
        return redirect(url_for('initial'))

    @app.route('/image/')
    def default_image(self):
        userID = request.args.get('userID')
        return monster_image(None, userID)

    @app.route('/image/<filename>')
    def image(self, filename):
        userID = request.args.get('userID')
        return monster_image(filename, userID)

    @app.route('/icon/')
    def default_icon(self):
        return self.get_icon(None)

    @app.route('/icon/<icon>')
    def get_icon(self, icon):
        return image_from_folder(icon, app.config['ICON_FOLDER'], "static/unknown_icon.svg")

    @app.route('/change_image', methods=(['POST']))
    def change_image(self):
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
