import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from config import Config
# Von Microblog uebernommen und nicht benoetigtes entfernt. Flask migrate upgrade Kommando hinzugefuegt, damit ein Google Cloud Deployment funktioniert.
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)

from app import routes, models, errors, api

migrate = Migrate(app, db)

# Flask db upgrade laufen lassen, damit in Google Cloud SQL die DB richtig aufgesetzt wird
with app.app_context():
    upgrade()

