import hashlib
import io
import os
import tempfile
import uuid
import datetime
from threading import Thread
from urllib.parse import urlparse

import flask
import itsdangerous
import qrcode
from PIL import ExifTags, Image
from flask_mail import Message
from itsdangerous import URLSafeSerializer, base64_encode
from werkzeug.utils import secure_filename
from wtforms import Label

from app.utils import is_face_detected, get_qr_file, threaded, sign_data
from flask import url_for, render_template, abort, redirect, send_file, request
from flask_admin.helpers import is_safe_url
from flask_login import current_user, login_user, login_required, logout_user

from app import app, db, photos, mail, hashids
from app.forms import LoginForm, UploadForm, PassportForm, CodeForm, EmailForm, PassVerifyForm
from app.models import Person, Pass
from settings import Config, SIGNER_SECRET_KEY


@app.route('/upload/', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    file_url = None
    if form.validate_on_submit():
        file = photos.save(form.photo.data, name=f'{uuid.uuid4()}.')
        src = urlparse(photos.url(file)).path

        # # Rotate image
        # path = os.path.join(os.path.abspath(os.path.dirname(__file__)), src)
        # image = Image.open(path)

        # for orientation in ExifTags.TAGS.keys():
        #     if ExifTags.TAGS[orientation] == 'Orientation':
        #         break
        # exif = dict(image._getexif().items())
        #
        # if exif[orientation] == 3:
        #     image = image.transpose(Image.ROTATE_180)
        # elif exif[orientation] == 6:
        #     image = image.transpose(Image.ROTATE_270)
        # elif exif[orientation] == 8:
        #     image = image.transpose(Image.ROTATE_90)
        #
        # image.save(src)
        # image.close()

        user = current_user
        if user:
            _pass = Pass(person_id=user.id, expire_at=datetime.date(1970,1,1))
            user.photo = src
            db.session.add(user)
            db.session.add(_pass)
            db.session.commit()
            return redirect(url_for('get_qr_code'))

    return render_template('upload.html', form=form, file_url=file_url)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Person.query.filter(Person.phone == form.phone.data).first()
        if not user:
            user = Person(phone=form.phone.data, active=True)
            db.session.add(user)
            db.session.commit()
        return redirect(url_for('confirm', phone=form.phone.data))

    return flask.render_template('login.html', form=form)


@app.route('/confirm/', methods=['GET', 'POST'])
def confirm():
    phone = request.args.get('phone')
    form = CodeForm(phone=phone)

    form.code.label = Label(field_id="code", text=f"На номер {phone[:6]}-***-**-{phone[-2:]} отправлен код подтверждения. Введите код")
    user = Person.query.filter(Person.phone == phone).first()

    if form.validate_on_submit():
        login_user(user)
        next = flask.request.args.get('next')
        if next:
            return flask.redirect(next)
        if user.photo is None:
            flask.redirect(url_for('upload'))

        return redirect(url_for('get_qr_code'))
    return flask.render_template('confirm.html', form=form, phone=phone)

#TODO: authorized for staff
@app.route('/qr_decode/<data>/', methods=['GET', 'POST'])
def qr_decode(data):
    s = URLSafeSerializer(SIGNER_SECRET_KEY, signer_kwargs={
        'key_derivation': 'hmac',
        'digest_method': hashlib.sha256
    })

    try:
        data = s.loads(data)
    except itsdangerous.exc.BadSignature:
        return 'HACKER DETECTED!!!!'

    id = hashids.decode(data.split('_')[0])
    name = ' '.join(data.split('_')[1:])
    person = Person.query.get(id)
    form = PassVerifyForm()

    if flask.request.method == 'POST':
        if form.validate_on_submit():
            _pass = Pass.query.filter_by(person_id=person.id).order_by(Pass.id.desc()).first()
            _pass.verified = True
            _pass.expire_at = form.expire_at.data
            db.session.add(_pass)
            db.session.commit()


    _pass = Pass.query.filter_by(person_id=person.id).order_by(Pass.id.desc()).first()

    if not person:
        abort(404)

    passport_num = person.passport_number if person.passport_number else ''

    return flask.render_template('qr_decode.html', person=person, passport_num=passport_num, _pass=_pass, form=form, name=name)


@login_required
@app.route('/person/',  methods=['GET', 'POST'])
def get_qr_code():
    form = PassportForm()
    person = db.session.query(Person).get(current_user.id)
    data_complete = False
    if not person:
        flask.abort(404)

    if flask.request.method == 'POST':
        if form.validate_on_submit():
            person.passport_number = form.passport_number.data
            db.session.add(person)
            db.session.commit()
            person = db.session.query(Person).get(current_user.id)

    if form.validate():
        data_complete = True

    return flask.render_template('person.html', person=person, form=form, data_complete=data_complete)



@app.route('/person/download_qr/')
@login_required
def qr_code_download():
    _id = hashids.encode(current_user.id)
    data = f"{_id}_{request.args.get('data')}"
    qr_file = get_qr_file(sign_data(data), 'JPEG')

    return send_file(qr_file.name,
                     mimetype='image/jpeg',
                     attachment_filename=qr_file.name,
                     as_attachment=True
                     )

@app.route('/person/pdf_qr/')
@login_required
def qr_code_pdf():
    _id = hashids.encode(current_user.id)
    data = f"{_id}_{request.args.get('data')}"
    qr_file = get_qr_file(sign_data(data), 'PDF')

    return send_file(qr_file.name,
                     mimetype='application/pdf',
                     attachment_filename=qr_file.name,
                     as_attachment=False
                     )


@app.route('/person/send_email/', methods=['GET', 'POST'])
def send_email():

    @threaded
    def send_async_email(msg):
        with app.app_context():
            mail.send(msg)

    email_form = EmailForm()
    if email_form.validate_on_submit():
        _id = hashids.encode(current_user.id)
        data = f"{_id}_{request.args.get('data')}"
        qr_file = get_qr_file(sign_data(data), 'JPEG')
        target_email = email_form.email.data
        message = Message('Электронный пропуск', sender=Config.MAIL_ADMIN, recipients=[target_email])
        message.body = 'Ваш электронный пропуск во вложении'
        with app.open_resource(qr_file.name) as fp:
            message.attach(qr_file.name, "image/jpeg", fp.read())
            with app.app_context():
                send_async_email(message)

        return flask.redirect(url_for('get_qr_code'))

    return flask.render_template('email_send.html', email_form=email_form, id=id)


#TODO: authorized for staff
@app.route('/person/<id>/verify/', methods=['GET', 'POST'])
def verify(id):
    person = db.session.query(Person).get(id)
    if not person:
        flask.abort(404)

    _pass =  Pass.query.filter_by(person_id=person.id).first()

    return flask.render_template('verify.html', person=person)

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('upload'))


@app.route('/')
def index():
    return redirect(url_for('upload'))

