from datetime import datetime
from typing import List

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from flask_sqlalchemy import SQLAlchemy

from Snackbar import db


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
    def username(self) -> string:
        if self.firstName and self.lastName:
            return '{} {}'.format(self.firstName, self.lastName)
        elif self.firstName:
            return '{}'.format(self.firstName)
        elif self.lastName:
            return '{}'.format(self.lastName)
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
@db.event.listens_for(User, 'before_delete')
def create_placeholder(mapper, connection, target):
    for hist in target.history:
        hist.user_placeholder = target.username 
        hist.userid = None 


class Item(db.Model):
    itemid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, default='')
    price: Mapped[float] = mapped_column(nullable=False)
    icon: Mapped[str] = mapped_column(String(300), nullable=True)

    history: Mapped[List["History"]] = relationship(back_populates="item")

    def __repr__(self):
        return self.name

@db.event.listens_for(Item, 'before_delete')
def create_placeholder(mapper, connection, target):
    for hist in target.history:
        hist.item_placeholder = target.name  
        hist.itemid = None  



class History(db.Model):
    historyid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'), nullable=True)
    user: Mapped["User"] = relationship(back_populates="history")
    user_placeholder = db.Column(db.String(80), nullable=True)
    
    @hybrid_property
    def username_or_placeholder(self):
        print(self.user)
        return self.user.username if self.user else self.user_placeholder

    itemid: Mapped[int] = mapped_column(ForeignKey('item.itemid'), nullable=True)
    item: Mapped["Item"] = relationship(back_populates="history")
    item_placeholder = db.Column(db.String(80), nullable=True)

    @hybrid_property
    def item_or_placeholder(self):
        return self.item.name if self.item else self.item_placeholder

    price: Mapped[float] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)

   

    def __repr__(self):
        return 'User {} ({} {}) bought {} for {} on the {}'.format(self.user, self.user.firstName, self.user.lastName,
                                                                   self.item, self.price, self.date)


class Inpayment(db.Model):
    paymentid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'), nullable=True)
    user: Mapped["User"] = relationship(back_populates="inpayment")

    amount: Mapped[float] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)
    notes: Mapped[str] = mapped_column(String(120), nullable=True)

    def __repr__(self):
        return 'User {} ({} {}) paid {} on the {}'.format(self.userid, self.user.firstName, self.user.lastName,
                                                          self.amount, self.date)


class Settings(db.Model):
    settingsid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(600), nullable=False)

    def __repr__(self):
        return self.key
