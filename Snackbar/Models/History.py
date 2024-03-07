from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Snackbar import db
from Snackbar.Models.Item import Item
from Snackbar.Models.User import User


class History(db.Model):
    historyid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'))
    user: Mapped["User"] = relationship(back_populates="history")

    itemid: Mapped[int] = mapped_column(ForeignKey('item.itemid'))
    item: Mapped["Item"] = relationship(back_populates="history")

    price: Mapped[float] = mapped_column()
    date: Mapped[datetime] = mapped_column()

    def __init__(self, user: User = None, item: Item = None, price: float = 0, date: datetime = None):
        self.user = user
        self.item = item
        self.price = price

        if date is None:
            date = datetime.now()
        self.date = date

    def __repr__(self):
        return 'User {} ({} {}) bought {} for {} on the {}'.format(self.user, self.user.firstName, self.user.lastName,
                                                                   self.item, self.price, self.date)
