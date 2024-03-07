import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool

app = Flask(__name__)

databaseName = 'data/CoffeeDB.db'
url = f"sqlite:///{app.root_path}/{databaseName}"
engine = create_engine(url, connect_args={'check_same_thread': False}, poolclass=SingletonThreadPool)
Session = sessionmaker(bind=engine)
session = Session()


app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = '123456790'
app.config['STATIC_FOLDER'] = 'static'
app.config['IMAGE_FOLDER'] = 'static/images'
app.config['ICON_FOLDER'] = 'static/icons'
app.config['DEBUG'] = False
app.config['SESSION_COOKIE_PATH'] = '/'

if not os.path.exists(app.config['IMAGE_FOLDER']):
    os.makedirs(app.config['IMAGE_FOLDER'])

db = SQLAlchemy(app)