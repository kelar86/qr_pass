import base64

import hashlib
import uuid
from datetime import datetime, date
from urllib.parse import urlparse

import flask
import itsdangerous
from PIL import Image, ImageOps
from flask import url_for, render_template, abort, redirect, send_file, request, jsonify, make_response, \
    send_from_directory
from flask_cors import cross_origin
from flask_login import current_user, login_user, login_required, logout_user
from flask_mail import Message
from wtforms import Label

from app import app, db, photos, mail, hashids, signer
from app.forms import LoginForm, UploadForm, PassportForm, CodeForm, EmailForm, PassVerifyForm
from app.models import Person, Pass
from app.utils import get_qr_file, threaded, sign_data, encode_data
from settings import Config


@app.route('/')
def index():
    return redirect(url_for('upload'))


@app.route('/upload/', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        user = current_user
        if user:
            file = photos.save(form.photo.data, name=f'{uuid.uuid4()}.')
            src = urlparse(photos.url(file)).path
            img = Image.open(photos.path(file))
            img = ImageOps.fit(img, (300, 400), Image.ANTIALIAS, 0, (0.5, 0.5))
            img.save(photos.path(file))
            _pass = Pass(person_id=user.id, expire_at=date(1970,1,1))
            user.photo = src
            db.session.add(user)
            db.session.add(_pass)
            db.session.commit()
            return redirect(url_for('get_qr_code'))

    return render_template('upload.html', form=form)


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
        if not user.photo:
            return flask.redirect(url_for('upload'))

        return redirect(url_for('get_qr_code'))
    return flask.render_template('confirm.html', form=form, phone=phone)


# TODO: authorized for staff
@app.route('/qr/<data>/', methods=['GET', 'POST'])
def qr_decode(data):
    data_str = base64.urlsafe_b64decode(data).decode("koi8-r")
    id = hashids.decode(data_str.split(':')[0])[0]
    person = Person.query.get(id)

    try:
        signer.verify_signature(data_str.encode(), person.signature)
    except itsdangerous.exc.BadSignature:
        return 'HACKER DETECTED!!!!'
    else:
        data = data_str

    name = ' '.join(data.split(':')[1:])
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
            _id = hashids.encode(current_user.id)
            data_string = f'{_id}:{form.name.data}:{form.f_name.data}:{form.second_name.data}'
            sign = signer.sign(data_string)
            person.signature = sign_data(sign)
            db.session.add(person)
            db.session.commit()
            person = db.session.query(Person).get(current_user.id)

    if form.validate():
        data_complete = True

    return flask.render_template('person.html', person=person, form=form, data_complete=data_complete)


@app.route('/person/download_qr/', defaults={'barcode_type': 'qr_code', 'img_format': 'JPEG'})
@app.route('/person/download_qr/<barcode_type>/<img_format>')
@login_required
def qr_code_download(barcode_type, img_format):
    _id = hashids.encode(current_user.id)
    data = f"{_id}:{request.args.get('data')}"
    qr_file = get_qr_file(encode_data(data), img_format, barcode_type)

    return send_file(qr_file.name,
                     mimetype='image/jpeg',
                     attachment_filename=qr_file.name,
                     as_attachment=True
                     )

@app.route('/person/pdf_qr/')
@login_required
def qr_code_pdf():
    _id = hashids.encode(current_user.id)
    data = f"{_id}:{request.args.get('data')}"
    qr_file = get_qr_file(encode_data(data), 'PDF')

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
        data = f"{_id}:{request.args.get('data')}"
        qr_file = get_qr_file(encode_data(data), 'JPEG')
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

    _pass = Pass.query.filter_by(person_id=person.id).first()
    return flask.render_template('verify.html', person=person)

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('upload'))


@app.route('/api/v1/decode/')
def api_decode():
    data = request.args.get('data')
    if not data:
        return abort(404)
    data_str = base64.urlsafe_b64decode(data).decode("koi8-r")
    hash_id = data_str.split(':')[0]
    id = hashids.decode(hash_id)[0]
    person = Person.query.get(id)

    try:
        signer.verify_signature(data_str.encode(), person.signature)
    except itsdangerous.exc.BadSignature:
        # BAD DATASTRING
        return abort(403)
    else:
        data = data_str

    name = ' '.join(data.split(':')[1:])
    _pass = Pass.query.filter_by(person_id=person.id).order_by(Pass.id.desc()).first()

    return jsonify(id=hash_id,
                   name=name,
                   photo=person.photo,
                   passport_number=person.passport_number,
                   expire_at=_pass.expire_at,
                   verified=_pass.verified
                   )


#TODO: authorized for staff

@app.route('/api/v1/person/<id>/pass/', methods=['POST'])
def api_verify(id):
    # # To resolve CORS problem
    params = request.get_json()
    if not params or not params['expire_at']:
        flask.abort(400)

    person = db.session.query(Person).get(hashids.decode(id)[0])

    if not person:
        flask.abort(404)

    _pass = Pass.query.filter_by(person_id=person.id).order_by(Pass.id.desc()).first()
    _pass.start_at = datetime.now()
    _pass.expire_at = datetime.strptime(params['expire_at'], '%Y-%m-%d')
    _pass.verified = True
    result = jsonify(
                     pass_id=_pass.id,
                     start_at=_pass.start_at,
                     expire_at=_pass.expire_at,
                     verified=_pass.verified)
    db.session.commit()

    return result
