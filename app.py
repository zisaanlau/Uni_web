# from flask import Flask,render_template
# from flask_sqlalchemy import SQLAlchemy
# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@Fengweiwangluo123@localhost:3306/alagen'
# db = SQLAlchemy(app)
# @app.route('/')
# def index():
#   return render_template('index.html')

# if __name__ == '__main__':
#   app.run(port=5023,host='0.0.0.0',debug=True)

from core import app
if __name__ == '__main__':
  app.run(port=5023)
