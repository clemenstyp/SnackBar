from datetime import datetime
from typing import List

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class Item(db.Model):
    itemid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, default='')
    price: Mapped[float] = mapped_column(nullable=False)
    icon: Mapped[str] = mapped_column(String(300), nullable=True)

    history: Mapped[List["History"]] = relationship(back_populates="item")

    def __repr__(self):
        return self.name


class History(db.Model):
    historyid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'))
    user: Mapped["User"] = relationship(back_populates="history")

    itemid: Mapped[int] = mapped_column(ForeignKey('item.itemid'))
    item: Mapped["Item"] = relationship(back_populates="history")

    price: Mapped[float] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)

    def __repr__(self):
        return 'User {} ({} {}) bought {} for {} on the {}'.format(self.user, self.user.firstName, self.user.lastName,
                                                                   self.item, self.price, self.date)


class Inpayment(db.Model):
    paymentid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'))
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
