import hashlib
import os

import flask
from flask import Flask, request, render_template
from flask_babelex import Babel
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, IMAGES, configure_uploads, patch_request_class
from hashids import Hashids
from itsdangerous import Signer

from settings import Config, ID_SALT, SIGNER_SECRET_KEY

app = Flask(__name__, static_folder='static')
cors = CORS(app)
app.config.from_object(Config)
# CORS settings
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CORS_METHODS'] = "GET,POST,OPTIONS"

app.secret_key = 'some_secret'
bootstrap = Bootstrap(app)

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)
hashids = Hashids(salt=ID_SALT, min_length=5)

signer = Signer(SIGNER_SECRET_KEY, key_derivation='hmac', digest_method=hashlib.sha512)

mail = Mail(app)

db = SQLAlchemy(app)
from app.models import *
db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Person.query.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return flask.redirect('/login')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


babel = Babel(app)
@babel.localeselector
def get_locale():
    from flask import session
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'ru')

from app import views, admin

# # Create a user to test with
# @app.before_first_request
# def create_user():
#     user_datastore.create_user(email='+79832907477')
#     db_session.session.coSmmit()
