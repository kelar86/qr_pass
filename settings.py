import os

basedir = os.path.abspath(os.path.dirname(__file__))


class FlaskUploadConfig:
    UPLOADS_DEFAULT_URL = 'http://localhost:8881/photos'
    UPLOADED_PHOTOS_DEST = os.path.dirname(__file__) + '/photos'
    UPLOADED_QR_DEST = os.path.dirname(__file__) + '/qr_codes'


class FlaskMailConfig:
    MAIL_SERVER = 'smtp.yandex.ru'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_PASSWORD = 'frhjkadqpwoqqpps'
    MAIL_USERNAME = 'qrpass@yandex.ru'
    MAIL_ADMIN = 'qrpass@yandex.ru'

class Config(FlaskUploadConfig, FlaskMailConfig):
    CSRF_ENABLED = True
    # SECRET_KEY = 'super secret key'
    FLASK_ADMIN_SWATCH = 'flatly'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "qrpass.db")}'

    SECURITY_LOGIN_USER_TEMPLATE = 'login.html'
    # MEDIA_PATH = os.path.join(basedir, "/images/")
    UPLOAD_FOLDER = os.path.join(basedir, "_uploads")



