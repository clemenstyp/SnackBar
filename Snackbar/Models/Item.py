from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Snackbar import db


class Item(db.Model):
    itemid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, default='')
    price: Mapped[float] = mapped_column()
    icon: Mapped[str] = mapped_column(String(300))

    history: Mapped[List["History"]] = relationship(back_populates="item")

    def __init__(self, name='', price=0):
        self.name = name
        self.price = price

    def __repr__(self):
        return self.name
