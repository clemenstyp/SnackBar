from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Snackbar import db
from Snackbar.Models.User import User


class Inpayment(db.Model):
    paymentid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'))
    user: Mapped["User"] = relationship(back_populates="inpayment")

    amount: Mapped[float] = mapped_column()
    date: Mapped[datetime] = mapped_column()
    notes: Mapped[str] = mapped_column(String(120))

    def __init__(self, user=None, amount=None, date=None, notes=None):
        self.user = user
        self.amount = amount
        self.notes = notes

        if date is None:
            date = datetime.now()
        self.date = date

    def __repr__(self):
        return 'User {} ({} {}) paid {} on the {}'.format(self.userid, self.user.firstName, self.user.lastName,
                                                          self.amount, self.date)
