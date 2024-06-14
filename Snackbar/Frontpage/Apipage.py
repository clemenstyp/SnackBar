import json
import traceback

import datetime
import os
import time
from flask import request, url_for, Response
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from Snackbar import app
from Snackbar.Helper.Database import get_coffee_dict
from Snackbar.Helper.Mailing import send_email
from Snackbar.Helper.Webhook import send_webhook
from Snackbar.models import History, Item, User, db


@app.get('/api/items')
def api_items():
    # docker überprüfen
    # und deployen
    try:
        items = list()
        for itemInstance in Item.query:
            items.append({'name': '{}'.format(itemInstance.name),
                          'price': itemInstance.price,
                          'itemid': '{}'.format(itemInstance.itemid),
                          'iconURL': '{}'.format(url_for('get_icon', _external=True, icon=itemInstance.icon))})

        response = Response(json.dumps(
            {"data": items, "message": "", "status": "ok"}), mimetype='application/json')
        response.status_code = 200
        return response

    except Exception as e:
        response = Response(json.dumps(
            {"data": "",
             "status": "error",
             "message": f"Some unknown error occured: Exception: {''.join(traceback.format_exception(e))}",
             }), mimetype='application/json')
        response.status_code = 400
        return response


@app.route('/api/info/<int:userid>', methods=['GET'])
def api_info_userid(userid):
    try:

        if userid is not None:
            curuser = db.session.get(User, userid)
        else:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "No userID provided.",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        if curuser is None:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "Could not find User. The userId is probably wrong. ",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        last_purchase = curuser.history[-1] if len(curuser.history) > 0 else None
        coffeeDict = get_coffee_dict(curuser, last_purchase, get_extra_data(request))

        response = Response(json.dumps(
            {"data": coffeeDict, "message": "", "status": "ok"}), mimetype='application/json')
        response.status_code = 200
        return response


    except Exception as e:
        response = Response(json.dumps(
            {"data": "",
             "status": "error",
             "message": f"Some unknown error occured: Exception: {''.join(traceback.format_exception(e))}",
             }), mimetype='application/json')
        response.status_code = 400
        return response


def get_extra_data(theRequest):
    return_data = {}
    if theRequest.environ.get('HTTP_X_FORWARDED_FOR') is not None:
        return_data["remote_address"] = theRequest.environ['HTTP_X_FORWARDED_FOR']
    elif theRequest.environ.get('REMOTE_ADDR') is not None:
        return_data["remote_address"] = theRequest.environ['REMOTE_ADDR']
    elif theRequest.remote_addr is not None:
        return_data["remote_address"] = theRequest.remote_addr

    if theRequest.referrer is not None:
        return_data["referrer"] = theRequest.referrer

    if theRequest.user_agent is not None:
        return_data["user_agent"] = theRequest.user_agent.string

    return return_data


@app.post('/api/info')
def api_info():
    # docker überprüfen
    # und deployen
    try:
        try:
            # Get the JSON data from the request
            data = request.get_json(force=True)
        except Exception as e:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": f"Content-Type not supported! Please use the JSON format.",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        userId = data.get('userId')
        userName = data.get('userName')
        if userId is not None:
            curuser = db.session.get(User, userId)
        elif userName is not None:
            name_array = userName.rsplit(" ", 1)
            if len(name_array) == 1:
                firstName = ""
                lastName = name_array[0]
            elif len(name_array) == 2:
                firstName = name_array[0]
                lastName = name_array[1]
            else:
                raise Exception
            curuser = db.session.query(User).filter(func.lower(User.firstName) == func.lower(firstName),
                                                    func.lower(User.lastName) == func.lower(lastName)).first()
            if curuser is None:
                with app.app_context():
                    newuser = User(firstName=firstName, lastName=lastName, email='', imageName='')
                    db.session.add(newuser)
                    db.session.commit()
                    db.session.flush()
                    db.session.refresh(newuser)

                    curuser = db.session.query(User).options(joinedload(User.history)).filter_by(
                        userid=newuser.userid).first()
                    # send_email_new_user(new_user)

        else:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "No userID or userName provided. Example Json: {\"userId\": someUserId } or {\"userName\": \"Firstname Lastname\" }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        if curuser is None:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "Could not find User. The userId is probably wrong. Example Json: {\"userId\": someUserId } or {\"userName\": \"Firstname Lastname\" }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        last_purchase = curuser.history[-1] if len(curuser.history) > 0 else None
        coffeeDict = get_coffee_dict(curuser, last_purchase, get_extra_data(request))

        response = Response(json.dumps(
            {"data": coffeeDict, "message": "", "status": "ok"}), mimetype='application/json')
        response.status_code = 200
        return response


    except Exception as e:
        response = Response(json.dumps(
            {"data": "",
             "status": "error",
             "message": f"Some unknown error occured: Exception: {''.join(traceback.format_exception(e))}",
             }), mimetype='application/json')
        response.status_code = 400
        return response


@app.post('/api/buy')
def api_buy():
    # docker überprüfen
    # und deployen
    try:
        try:
            # Get the JSON data from the request
            data = request.get_json(force=True)
        except Exception as e:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": f"Content-Type not supported! Please use the JSON format.",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        userId = data.get('userId')
        userName = data.get('userName')
        if userId is not None:
            curuser = db.session.get(User, userId)
        elif userName is not None:
            name_array = userName.rsplit(" ", 1)
            if len(name_array) == 1:
                firstName = ""
                lastName = name_array[0]
            elif len(name_array) == 2:
                firstName = name_array[0]
                lastName = name_array[1]
            else:
                raise Exception
            curuser = db.session.query(User).filter(func.lower(User.firstName) == func.lower(firstName),
                                                    func.lower(User.lastName) == func.lower(lastName)).first()
            if curuser is None:
                with app.app_context():
                    newuser = User(firstName=firstName, lastName=lastName, email='', imageName='')
                    db.session.add(newuser)
                    db.session.commit()
                    db.session.flush()
                    db.session.refresh(newuser)

                    curuser = db.session.query(User).options(joinedload(User.history)).filter_by(
                        userid=newuser.userid).first()
                # send_email_new_user(new_user)

        else:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "No userID or userName provided. Example Json: {\"userId\": someUserId, \"itemId\": someItemId } or {\"userName\": \"Firstname Lastname\", \"itemId\": someItemId }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        if curuser is None:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "Could not find User. The userId is probably wrong. Example Json: {\"userId\": someUserId, \"itemId\": someItemId } or {\"userName\": \"Firstname Lastname\", \"itemId\": someItemId }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        itemId = data.get('itemId')
        if itemId is None:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "No itemId provided. Example Json: {\"userId\": someUserId, \"itemId\": someItemId } or {\"userName\": \"Firstname Lastname\", \"itemId\": someItemId }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        curitem = db.session.get(Item, itemId)
        if curitem is None:
            response = Response(json.dumps(
                {"data": "",
                 "status": "error",
                 "message": "Could not find Item. The itemId is probably wrong. Example Json: {\"userId\": someUserId, \"itemId\": someItemId } or {\"userName\": \"Firstname Lastname\", \"itemId\": someItemId }",
                 }), mimetype='application/json')
            response.status_code = 400
            return response

        user_purchase = History(user=curuser, item=curitem, price=curitem.price)

        db.session.add(user_purchase)
        db.session.commit()

        send_email(curuser, curitem)
        coffeeDict = get_coffee_dict(curuser, user_purchase, get_extra_data(request))

        # log_path
        root_path = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(root_path, "../../data/buy")
        if not os.path.exists(log_path):
            os.makedirs(log_path)



        for filename in os.listdir(log_path):
            filestamp = os.stat(os.path.join(log_path, filename)).st_mtime
            two_weeks_ago = time.time() - 14 * 86400
            if filestamp < two_weeks_ago:
                os.remove(os.path.join(log_path, filename))

        log_name = f"{datetime.date.today().strftime('%Y-%m-%d')}.txt"
       
        with open(os.path.join(log_path, log_name), 'a') as log_file:
            print(f'{datetime.datetime.now().replace(microsecond=0).isoformat()}: /api/buy called: ', file=log_file)
            print(json.dumps(coffeeDict, indent=4), file=log_file)


        try:
            send_webhook(coffeeDict)
        except:
            pass

        response = Response(json.dumps(
            {"data": coffeeDict, "message": "", "status": "ok"}), mimetype='application/json')
        response.status_code = 200
        return response


    except Exception as e:
        response = Response(json.dumps(
            {"data": "",
             "status": "error",
             "message": f"Some unknown error occured: Exception: {''.join(traceback.format_exception(e))}",
             }), mimetype='application/json')
        response.status_code = 400
        return response
