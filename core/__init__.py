import os
from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
from concurrent.futures import ThreadPoolExecutor
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost:3306/aiagen'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_COMMIT_TEARDOWN'] = True
db = SQLAlchemy(app)
executor = ThreadPoolExecutor(2)

from core import views, errors