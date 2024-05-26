import csv
import os
from datetime import date, datetime

from flask import url_for
from sqlalchemy import func, and_, extract

from Snackbar import app, databaseName
from Snackbar.Helper.Appearance import button_background, button_font_color
#from Snackbar.models import Coffeeadmin, History, Inpayment, Item, Settings, User
from Snackbar.models import *


def database_exist():
    if not os.path.isfile(databaseName):
        return False
    return True


def get_users_with_leaders():
    initusers = list()
    with app.app_context():
        all_items = Item.query.filter(Item.icon is not None, Item.icon != '', Item.icon != ' ')
        all_items_id = [int(instance.itemid) for instance in all_items]
        if len(all_items_id) > 0:
            itemid = all_items_id[0]
        else:
            itemid = ''

        leader_data = get_all_leader_data()

        for aUser in User.query.filter(User.hidden.is_(False)):
            initusers.append({'firstName': '{}'.format(aUser.firstName),
                              'lastName': '{}'.format(aUser.lastName),
                              'imageName': '{}'.format(aUser.imageName),
                              'id': '{}'.format(aUser.userid),
                              'bgcolor': '{}'.format(button_background(f"{aUser.firstName} {aUser.lastName}".strip())),
                              'fontcolor': '{}'.format(
                                  button_font_color(f"{aUser.firstName} {aUser.lastName}.strip()")),
                              'coffeeMonth': get_unpaid(aUser.userid, itemid, leader_data),
                              'leader': get_leader(aUser.userid, leader_data),
                              'email': '{}'.format(aUser.email),
                              })
    return initusers


def get_all_leader_data():
    leader_data = {}
    with app.app_context():
        all_items = Item.query.filter(Item.icon is not None, Item.icon != '', Item.icon != ' ')
        for aItem in all_items:
            leader_ids = get_leaders_from_database(aItem.itemid)

            item_data = {'leader_ids': leader_ids, 'icon': aItem.icon}
            leader_data[aItem.itemid] = item_data

    return leader_data


def get_leaders_from_database(itemid):
    with app.app_context():
        tmp_query = db.session.query(User.userid, func.count(History.price), func.max(History.date))
        tmp_query = tmp_query.outerjoin(History, and_(User.userid == History.userid, History.itemid == itemid,
                                                      extract('month', History.date) == datetime.now().month,
                                                      extract('year', History.date) == datetime.now().year))
        tmp_query = tmp_query.group_by(User.userid)
        tmp_query = tmp_query.order_by(func.count(History.price).desc())
        tmp_query = tmp_query.order_by(History.date)
        tmp_query = tmp_query.all()

        return tmp_query


def get_unpaid(userid, itemid, leader_data):
    returnValue = 0
    if itemid in leader_data:
        item_data = leader_data[itemid]['leader_ids']

        user_ids = [x[0] for x in item_data]
        item_sums = [x[1] for x in item_data]

        try:
            idx = user_ids.index(userid)
            returnValue = item_sums[idx]
        except (TypeError, ValueError):
            pass

    return returnValue


def get_leader(userid, leader_data):
    leader_info = list()
    i = 0
    for itemid in sorted(leader_data.keys()):
        item_data = leader_data[itemid]
        item_leader = item_data['leader_ids']
        if len(item_leader) > 0:
            winner = item_leader[0]
            winner_id = winner[0]
            winner_count = winner[1]
            if int(winner_id) == userid and winner_count > 0:
                item_id = int(itemid)
                icon_file = str(item_data['icon'])
                position = (-7 + (i * 34))
                leader_info.append({"item_id": item_id, "icon": icon_file, "position": position})
                i = i + 1

    return leader_info


def get_rank(userid, itemid, leader_data):
    rank = 0
    lowerbound = None
    upperbound = None
    if itemid in leader_data:
        item_data = leader_data[itemid]['leader_ids']

        user_id = [x[0] for x in item_data]
        item_sum = [x[1] for x in item_data]

        idx = user_id.index(userid)
        rank = idx + 1

        if rank == len(user_id):
            upperbound = item_sum[idx - 1] - item_sum[idx] + 1
            lowerbound = None

        elif rank == 1:
            upperbound = None
            lowerbound = item_sum[idx] - item_sum[idx + 1] + 1

        else:
            upperbound = item_sum[idx - 1] - item_sum[idx] + 1
            lowerbound = item_sum[idx] - item_sum[idx + 1] + 1

    return {'rank': rank,
            'upperbound': upperbound,
            'lowerbound': lowerbound}


def get_total(userid, itemid):
    with app.app_context():
        n_unpaid = db.session.query(History). \
            filter(History.userid == userid). \
            filter(History.itemid == itemid).count()

        if n_unpaid is None:
            n_unpaid = 0

        return n_unpaid


def build_sample_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        with open('defaultUserList.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                firstName = '{}'.format(row['FirstName'])
                lastName = '{}'.format(row['LastName'])
                imageName = '{}'.format(row['ImageName'])
                email = '{}'.format(row['email'])
                newuser = User(firstName=firstName, lastName=lastName, email=email, imageName=imageName)
                db.session.add(newuser)

        itemname = ['Coffee', 'Water', 'Snacks', 'Cola']
        price = [0.2, 0.55, 0.2, 0.4]

        for i in range(len(itemname)):
            newitem = Item(name='{}'.format(itemname[i]), price=float('{}'.format(price[i])))
            newitem.icon = "item" + str(i + 1) + ".svg"
            # newitem.name = itemname[i]
            # newitem.price = price[i]
            db.session.add(newitem)

        newadmin = Coffeeadmin(name='admin', password='admin', send_bill=False, email='')
        db.session.add(newadmin)

        db.session.commit()
    return


def set_default_settings():
    with app.app_context():
        with open('defaultSettings.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = '{}'.format(row['key'])
                db_entry = db.session.query(Settings).filter_by(key=key).first()
                if db_entry is None:
                    newsettingitem = Settings(key='{}'.format(row['key']), value='{}'.format(row['value']))
                    db.session.add(newsettingitem)

        db.session.commit()


def settings_for(key):
    with app.app_context():
        db_entry = db.session.query(Settings).filter_by(key=key).first()
        if db_entry is None:
            return ''
        else:
            return db_entry.value


def get_coffee_dict(curuser: User, last_purchase: History | None = None, extra_data=None):
    if extra_data is None:
        extra_data = {}
    leader_data = get_all_leader_data()

    curn_bill_float = curuser.calculate_account_balance()

    minimum_balance = float(settings_for('minimumBalance'))
    if curn_bill_float <= minimum_balance:
        shouldTopUpMoney = True
    else:
        shouldTopUpMoney = False

    coffeeDict = {"firstName": curuser.firstName, "lastName": curuser.lastName, "userId": curuser.userid,
                  "name": '{} {}'.format(curuser.firstName, curuser.lastName), "balance": round(curn_bill_float, 2),
                  "shouldTopUpMoney": shouldTopUpMoney,
                  "userPage": url_for('user_page', _external=True, userid=curuser.userid)}

    purchaseDict = {}

    if last_purchase:
        purchaseDict["item"] = last_purchase.item.name
        purchaseDict["itemId"] = last_purchase.item.itemid
        purchaseDict["price"] = last_purchase.price
        purchaseDict["purchaseDate"] = last_purchase.date.astimezone().replace(microsecond=0).isoformat()
        purchaseDict["monthlyCount"] = get_unpaid(curuser.userid, last_purchase.itemid, leader_data)
        purchaseDict["totalCount"] = get_total(curuser.userid, last_purchase.itemid)

    coffeeDict["last_purchase"] = purchaseDict

    coffeeDict["extra_data"] = extra_data

    return coffeeDict


def get_total_bill():
    def nextMonth(currentMonth):
        if currentMonth.month == 12:  # New year
            return date(currentMonth.year + 1, 1, 1)
        else:
            return date(currentMonth.year, currentMonth.month + 1, 1)

    def prevMonth(currentMonth):
        if currentMonth.month == 1:  # New year
            return date(currentMonth.year - 1, 12, 1)
        else:
            return date(currentMonth.year, currentMonth.month - 1, 1)

    def months_between(date_start, date_end):
        months = []

        # Make sure start_date is smaller than end_date
        if date_start > date_end:
            tmp = date_start
            date_start = date_end
            date_end = tmp

        tmp_date = date_start
        while tmp_date.month <= date_end.month or tmp_date.year < date_end.year:
            months.append(
                tmp_date)  # Here you could do for example: months.append(datetime.datetime.strftime(tmp_date, "%b '%y"))
            tmp_date = nextMonth(tmp_date)

        return months

    with app.app_context():
        currentDay = datetime.now()
        newestDate = nextMonth(date(currentDay.year, currentDay.month, currentDay.day))
        oldestDate = prevMonth(newestDate)

        for instance in Inpayment.query.order_by(Inpayment.date).limit(1):
            oldestDateInpayment = date(instance.date.year, instance.date.month, 1)
            if oldestDateInpayment < oldestDate:
                oldestDate = oldestDateInpayment

        for instance in History.query.order_by(History.date).limit(1):
            oldestDateHistory = date(instance.date.year, instance.date.month, 1)
            if oldestDateHistory < oldestDate:
                oldestDate = oldestDateHistory

        total_cash = 0
        total_open = 0
        accounting = list()

        for month in months_between(oldestDate, newestDate):
            total_open = 0

            previousMonth = prevMonth(month)
            for instance in Inpayment.query.filter(Inpayment.date.between(previousMonth, month)):
                total_cash += instance.amount

            for instance in User.query.filter(User.hidden.is_(False)):
                curr_bill = 0
                for historyInstance in History.query.filter(
                        and_(History.date.between(oldestDate, month), History.userid == instance.userid)):
                    curr_bill += historyInstance.price

                total_payment = 0
                for inpaymentInstance in Inpayment.query.filter(
                        and_(Inpayment.date.between(oldestDate, month), Inpayment.userid == instance.userid)):
                    total_payment += inpaymentInstance.amount

                total_open -= -curr_bill + total_payment

            accounting.append({'name': '{}'.format(previousMonth.strftime('%B %Y')),
                               'from_date': '{}'.format(previousMonth),
                               'to_date': '{}'.format(month),
                               'cash': total_cash,
                               'open': total_open,
                               'sum': (total_cash + total_open)})

        return accounting, total_cash
