from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from Snackbar import db


class Settings(db.Model):
    settingsid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(80), unique=True)
    value: Mapped[str] = mapped_column(String(600))

    def __init__(self, key='', value=''):
        if not key:
            key = ''
        if not value:
            value = ''

        self.key = key
        self.value = value

    def __repr__(self):
        return self.key
