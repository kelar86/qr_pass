import io
import os
import tempfile
import uuid
from urllib.parse import urlparse

import flask
import qrcode
from PIL import ExifTags, Image
from werkzeug.utils import secure_filename
from wtforms import Label

from app.utils import is_face_detected
from flask import url_for, render_template, abort, redirect, send_file, request
from flask_admin.helpers import is_safe_url
from flask_login import current_user, login_user, login_required, logout_user

from app import app, db, photos
from app.forms import LoginForm, UploadForm, PassportForm, CodeForm
from app.models import Person, Pass


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
            _pass = Pass(person_id=user.id)
            user.photo = src
            db.session.add(user)
            db.session.add(_pass)
            db.session.commit()
            return redirect(url_for('get_qr_code', id=user.id))

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
        return flask.redirect(next) if next else redirect(url_for('upload'))

    return flask.render_template('confirm.html', form=form, phone=phone)


@app.route('/qr_decode/<id>/', methods=['GET', 'POST'])
def qr_decode(id):
    form = PassportForm()
    person = Person.query.get(id)

    #TODO: add period and actual filtering for pass
    _pass = Pass.query.filter_by(person_id=person.id).first()

    if not person:
        abort(404)

    passport_num = person.passport_number if person.passport_number else ''

    if form.validate_on_submit():
        person.passport_number = form.passport_number.data
        db.session.add(person)
        db.session.commit()

    return flask.render_template('qr_decode.html', form=form, person=person, passport_num=passport_num, _pass=_pass)


@app.route('/person/<id>/',  methods=['GET', 'POST'])
def get_qr_code(id):
    form = PassportForm()
    person = db.session.query(Person).get(id)
    if not person:
        flask.abort(404)

    if form.validate_on_submit():
        person.passport_number = form.passport_number.data
        db.session.add(person)
        db.session.commit()

    return flask.render_template('person.html', person=person, form=form)

@app.route('/person/<id>/download_qr/')
def qr_code_download(id):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    url = f'{flask.request.host_url}qr_decode/{id}/'
    qr.add_data(url)

    t_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.jpg')
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(t_file, format='JPEG')
    t_file.seek(0)

    return send_file(t_file.name,
                     mimetype='image/jpeg',
                     attachment_filename=t_file.name,
                     as_attachment=True
                     )


@app.route('/person/<id>/pdf_qr/')
def qr_code_pdf(id):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    url = f'{flask.request.host_url}qr_decode/{id}/'
    qr.add_data(url)
    img = qr.make_image(fill_color="black", back_color="white")
    t_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.pdf')
    img.save(t_file, format='PDF', resolution=100.0)
    t_file.seek(0)

    return send_file(t_file.name,
                     mimetype='application/pdf',
                     attachment_filename=t_file.name,
                     as_attachment=False
                     )


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('upload'))


@app.route('/')
def index():
    return redirect(url_for('upload'))

