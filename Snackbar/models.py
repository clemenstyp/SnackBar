from datetime import datetime
from typing import List

from sqlalchemy import String, ForeignKey, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from flask_sqlalchemy import SQLAlchemy

from Snackbar import app
db = SQLAlchemy(app)

class Coffeeadmin(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, default='')
    password: Mapped[str] = mapped_column(String(64))
    send_bill: Mapped[bool] = mapped_column(default=False)
    email: Mapped[str] = mapped_column(String(120), default='')

    # Flask-Login integration
    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.id


class User(db.Model):
    userid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    firstName: Mapped[str] = mapped_column(String(80), nullable=True, default='')
    lastName: Mapped[str] = mapped_column(String(80), nullable=False, default='')
    imageName: Mapped[str] = mapped_column(String(240), nullable=True, default='')
    email: Mapped[str] = mapped_column(String(120), nullable=True, default='')
    hidden: Mapped[bool] = mapped_column(default=False)

    inpayment: Mapped[List["Inpayment"]] = relationship(back_populates="user")
    history: Mapped[List["History"]] = relationship(back_populates="user")

    @hybrid_property
    def username(self):
        if self.firstName and self.lastName:
            return 'F:{} L:{}'.format(self.firstName, self.lastName)
        elif self.firstName:
            return 'F:{}'.format(self.firstName)
        elif self.lastName:
            return 'L:{}'.format(self.lastName)
        else:
            return 'Unknown User'
            
    def __repr__(self):
        return '{} {}'.format(self.firstName, self.lastName)

    def get_payment(self):
        total_payment = round(sum(inpayment.amount for inpayment in self.inpayment), 2)
        if total_payment is None:
            total_payment = 0
        return total_payment

    def get_current_bill(self):
        current_bill = round(sum(history.price for history in self.history), 2)
        if current_bill is None:
            current_bill = 0

        return current_bill

    def calculate_account_balance(self):
        curr_bill = self.get_current_bill()
        total_payment = self.get_payment()

        account_balance = -curr_bill + total_payment

        return account_balance

# Event listener für das Löschen eines Benutzers
@event.listens_for(User, "before_delete")
def create_user_placeholder(mapper, connection, target):
    print(f"before delete create_user_placeholder target: {target} - target.firstName: {target.firstName} - target.username: {target.username}")
    for hist in target.history:
        print(f"hist: {hist}")
        hist.user_placeholder = f"T:{target.username}" 

    for inpay in target.inpayment:
        inpay.user_placeholder = target.username 

class Item(db.Model):
    itemid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, default='')
    price: Mapped[float] = mapped_column(nullable=False)
    icon: Mapped[str] = mapped_column(String(300), nullable=True)

    history: Mapped[List["History"]] = relationship(back_populates="item")

    def __repr__(self):
        return self.name

@event.listens_for(Item, "before_delete")
def create_item_placeholder(mapper, connection, target):
    print("before delete create_item_placeholder")
    for hist in target.history:
        hist.item_placeholder = target.name  

class History(db.Model):
    historyid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'), nullable=True)
    user: Mapped["User"] = relationship(back_populates="history")
    user_placeholder = db.Column(db.String(80), nullable=True)
    
    @hybrid_property
    def username_or_placeholder(self):
        if self.user:
            if hasattr(self.user, 'username'):
                return self.user.username
        return self.user_placeholder

    itemid: Mapped[int] = mapped_column(ForeignKey('item.itemid'), nullable=True)
    item: Mapped["Item"] = relationship(back_populates="history")
    item_placeholder = db.Column(db.String(80), nullable=True)

    @hybrid_property
    def item_or_placeholder(self):
        if self.item:
            if hasattr(self.item, 'name'):
                return self.item.name
        return self.item_placeholder

    price: Mapped[float] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)

   

    def __repr__(self):
        return 'User {} bought {} for {} on the {}'.format(self.username_or_placeholder, self.item_or_placeholder, self.price, self.date)


class Inpayment(db.Model):
    paymentid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'), nullable=True)
    user: Mapped["User"] = relationship(back_populates="inpayment")
    user_placeholder = db.Column(db.String(80), nullable=True)
    
    @hybrid_property
    def username_or_placeholder(self):
        if self.user:
            if hasattr(self.user, 'username'):
                return self.user.username
        return self.user_placeholder

    amount: Mapped[float] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)
    notes: Mapped[str] = mapped_column(String(120), nullable=True)

    def __repr__(self):
        return 'User {} ({}) paid {} on the {}'.format(self.userid, self.username_or_placeholder, self.amount, self.date)


class Settings(db.Model):
    settingsid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(600), nullable=False)

    def __repr__(self):
        return self.key
