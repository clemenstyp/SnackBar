from typing import List

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Snackbar import db
from Snackbar.Models.History import History
from Snackbar.Models.Inpayment import Inpayment


class User(db.Model):
    userid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    firstName: Mapped[str] = mapped_column(String(80), nullable=False, default='')
    lastName: Mapped[str] = mapped_column(String(80), nullable=False, default='')
    imageName: Mapped[str] = mapped_column(String(240), nullable=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, default='')
    hidden: Mapped[bool] = mapped_column()

    inpayment: Mapped[List["Inpayment"]] = relationship(back_populates="user")
    history: Mapped[List["History"]] = relationship(back_populates="user")

    def __init__(self, firstname='', lastname='', email='', imagename=''):
        if not firstname:
            firstname = ''
        if not lastname:
            lastname = ''
        if not imagename:
            imagename = ''
        if not email:
            email = ''

        self.hidden = False
        self.firstName = firstname
        self.lastName = lastname
        self.imageName = imagename
        self.email = email

    def __repr__(self):
        return '{} {}'.format(self.firstName, self.lastName)

    def get_payment(self):
        total_payment = db.session.query(func.sum(Inpayment.amount)).filter(self.inpayment).scalar()
        if total_payment is None:
            total_payment = 0
        return total_payment

    def get_current_bill(self):
        curr_bill = db.session.query(func.sum(History.price)).filter(self.history).scalar()
        if curr_bill is None:
            curr_bill = 0

        return curr_bill

    def calculate_account_balance(self):
        curr_bill = self.get_current_bill()
        total_payment = self.get_payment()

        account_balance = -curr_bill + total_payment

        return account_balance
