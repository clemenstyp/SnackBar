from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

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
