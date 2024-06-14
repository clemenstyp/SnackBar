from datetime import datetime
from typing import List

from sqlalchemy import String, ForeignKey, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.hybrid import hybrid_property
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import case
from sqlalchemy import select
from sqlalchemy import and_
from Snackbar import app
db = SQLAlchemy(app)

# # sql alchemy debug logging:
# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class Coffeeadmin(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, default='')
    password: Mapped[str] = mapped_column(String(64), nullable=True)
    send_bill: Mapped[bool] = mapped_column(default=False)
    email: Mapped[str] = mapped_column(String(120), default='', nullable=True)

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
            return self.firstName + " " + self.lastName
        elif self.firstName:
            return self.firstName
        elif self.lastName:
            return self.lastName
        else:
            return 'Unknown User'
    
    @username.inplace.expression
    @classmethod
    def _username_expression(cls):
        return case(
            (and_(cls.firstName != None, cls.lastName != None), cls.firstName + " " + cls.lastName),
            (cls.firstName != None, cls.firstName),
            (cls.lastName != None, cls.lastName),
            else_='Unknown User'
        )

    
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

@event.listens_for(Session, 'before_flush')
def database_flush(session, flush_context, instances):
    for p_object in session.deleted:
        if isinstance(p_object, User):
            # print(f"before flush / delete  user target: {p_object} - target.firstName: {p_object.firstName} - target.username: {p_object.username}")
            for hist in p_object.history:
                hist.user_placeholder = p_object.username
            for inpay in p_object.inpayment:
                # print(f"hist: {inpay}")
                inpay.user_placeholder = p_object.username
        elif isinstance(p_object, Item):
            # print(f"before flush / delete  item target: {p_object}")
            for hist in p_object.history:
                hist.item_placeholder = p_object.name  
        # else:
        #     print(f"before flush / delete  other target: {p_object}")
            

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

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'), nullable=True)
    user: Mapped["User"] = relationship(back_populates="history")
    user_placeholder: Mapped[str] = mapped_column(String(80), nullable=True)
    
    @hybrid_property
    def username_or_placeholder(self):
        if self.user:
            if hasattr(self.user, 'username'):
                return self.user.username
        return self.user_placeholder

    #@username_or_placeholder.inplace.expression
    @classmethod
    def _username_or_placeholder_expression(cls):
        return case(
            (cls.user != None, select(User).where(User.userid == cls.userid).first().firstName + " " + select(User).where(User.userid == cls.userid).first().lastName),
            else_=cls.user_placeholder
        )

    itemid: Mapped[int] = mapped_column(ForeignKey('item.itemid'), nullable=True)
    item: Mapped["Item"] = relationship(back_populates="history")
    item_placeholder: Mapped[str] = mapped_column(String(80), nullable=True)

    @hybrid_property
    def item_or_placeholder(self):
        if self.item:
            if hasattr(self.item, 'name'):
                return self.item.name
        return self.item_placeholder

    @item_or_placeholder.inplace.expression
    @classmethod
    def _item_or_placeholder_expression(cls) -> SQLColumnExpression[str]:
        return case(
            (cls.item != None, 
             select(Item.name)
             .where(Item.itemid == cls.itemid)
             .scalar_subquery()
            ),
            else_=cls.item_placeholder
        )
    
    price: Mapped[float] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)

   

    def __repr__(self):
        return 'User {} bought {} for {} on the {}'.format(self.username_or_placeholder, self.item_or_placeholder, self.price, self.date)


class Inpayment(db.Model):
    paymentid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[int] = mapped_column(ForeignKey('user.userid'), nullable=True)
    user: Mapped["User"] = relationship(back_populates="inpayment")
    user_placeholder: Mapped[str] = mapped_column(String(80), nullable=True)
    
    @hybrid_property
    def username_or_placeholder(self):
        if self.user:
            if hasattr(self.user, 'username'):
                return self.user.username
        return self.user_placeholder

    #@username_or_placeholder.inplace.expression
    @classmethod
    def _username_or_placeholder_expression(cls):
        return case(
            (cls.user != None, select(User).where(User.userid == cls.userid).first().firstName + " " + select(User).where(User.userid == cls.userid).first().lastName),
            else_=cls.user_placeholder
        )
    
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
