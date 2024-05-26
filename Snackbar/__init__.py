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
database_url = f"sqlite:///{databaseName}"
engine = create_engine(database_url, connect_args={'check_same_thread': False}, poolclass=SingletonThreadPool)
Session = sessionmaker(bind=engine)
session = Session()

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['STATIC_FOLDER'] = os.path.join(root_folder, "static")
app.config['IMAGE_FOLDER'] = os.path.join(app.instance_path, 'user')
app.config['ICON_FOLDER'] = os.path.join(app.instance_path, 'icons')
app.config['DEBUG'] = False

if not os.path.exists(app.config['IMAGE_FOLDER']):
    os.makedirs(app.config['IMAGE_FOLDER'])

#db = SQLAlchemy(app)
