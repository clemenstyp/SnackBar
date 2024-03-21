import os
import pathlib

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool

root_folder = pathlib.Path(__file__).parent.parent.resolve()

app = Flask(__name__, instance_path=os.path.join(root_folder, "data"), root_path=root_folder)

databaseFile = 'CoffeeDB.db'
databaseName = os.path.join(app.instance_path, databaseFile)
url = f"sqlite:///{databaseName}"
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
