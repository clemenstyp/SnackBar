import os
import threading
import time
from datetime import datetime

import schedule
from backports import csv
from sqlalchemy.sql import func

from Snackbar import app, db
from Snackbar.Helper.Mailing import send_bill_to, send_reminder
from Snackbar.models import Coffeeadmin, Inpayment, User

running = True
schedule_thread = None


def setup_schedule():
    schedule.every().monday.at("10:30").do(send_reminder_to_all)
    schedule.every().monday.at("00:00").do(send_bill_to_admin)


def start_schedule():
    print("Starting Scheduler")
    global schedule_thread
    schedule_thread = threading.Thread(target=run_schedule).start()


def stop_schedule():
    global running
    running = False


def run_schedule():
    global running
    while running is True:
        schedule.run_pending()
        time.sleep(1)


def send_reminder_to_all():
    with app.app_context():
        try:
            for aUser in User.query.filter(User.hidden.is_(False)):
                send_reminder(aUser)
        except:
            pass


def send_bill_to_admin():
    with app.app_context():
        total_cash, total_bill, users, bill_date = create_bill()
        save_bill(total_cash, total_bill, bill_date)

        try:
            for aAdmin in Coffeeadmin.query.filter(Coffeeadmin.send_bill.is_(True)):
                send_bill_to(aAdmin, total_cash, total_bill, users, bill_date)
        except:
            pass


def create_bill():
    with app.app_context():
        initusers = list()
        total_bill = 0
        total_cash = db.session.query(func.sum(Inpayment.amount)).scalar()

        for aUser in User.query.filter(User.hidden.is_(False)):
            bill = aUser.calculate_account_balance()
            total_bill += bill
            initusers.append({'name': '{} {}'.format(aUser.firstName, aUser.lastName),
                              'userid': '{}'.format(aUser.userid),
                              'bill': bill})

        users = sorted(initusers, key=lambda k: k['name'])

        bill_date = datetime.now()

        return total_cash, total_bill, users, bill_date


def save_bill(total_cash, total_bill, bill_date):
    # filename = 'CoffeeBill_{}_{}.csv'.format(bill_date.date().isoformat(),bill_date.time().strftime('%H-%M-%S'))
    filename = 'CoffeeBill.csv'

    # export_path
    root_path = os.path.dirname(os.path.abspath(__file__))
    export_path = os.path.join(root_path, "bill")
    if not os.path.exists(export_path):
        os.makedirs(export_path)

    full_export_path = os.path.join(export_path, filename)

    # check if export file already exists (if not then create it and add header)
    if not os.path.exists(full_export_path):
        # create file
        with open(full_export_path, "w") as file:
            writer = csv.writer(file)
            # Daten an die CSV-Datei anhängen
            writer.writerow(["Date", "Total Cash", "Total Open Bill", "Resulting Sum"])

    today = bill_date.strftime('%Y-%m-%d %H-%M-%S')
    # Append to CSV file
    with open(full_export_path, mode="a", newline="") as file:
        writer = csv.writer(file)

        # Daten an die CSV-Datei anhängen
        writer.writerow([today, "{:0.2f}".format(total_cash), "{:0.2f}".format(total_bill),
                         "{:0.2f}".format((total_cash - total_bill))])
