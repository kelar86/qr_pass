import flask
from flask import Flask, request, render_template
from flask_babelex import Babel
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, IMAGES, configure_uploads, patch_request_class
from settings import Config

app = Flask(__name__, static_url_path='/static')
app.config.from_object(Config)
app.secret_key = 'some_secret'
bootstrap = Bootstrap(app)

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)


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
