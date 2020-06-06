import tempfile
import uuid
from urllib.parse import urlparse

import flask
import qrcode
from app import app, db, photos
from app.forms import LoginForm, UploadForm
from app.models import User
from flask import url_for, render_template, abort, redirect, send_file
from flask_admin.helpers import is_safe_url
from flask_login import current_user, login_user, login_required, logout_user


@app.route('/upload/', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    file_url = None
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        file_url = photos.url(filename)
        src = urlparse(file_url).path
        user = current_user
        if user:
            user.photo = src
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('get_qr_code', id=user.id))

    return render_template('upload.html', form=form, file_url=file_url)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():

        user = User.query.filter(User.phone == form.phone.data).first()

        if not user:
            _id = str(uuid.uuid1())
            user = User(id=_id, phone=form.phone.data, active=True)
            db.session.add(user)
            db.session.commit()

        login_user(user)

        next = flask.request.args.get('next')
        if next and not is_safe_url(next):
            return flask.abort(400)
        return flask.redirect(next) if next else redirect(url_for('upload'))

    return flask.render_template('login.html', form=form)


@app.route('/user/<id>/qrcode/')
def get_qr_code(id):
    user = db.session.query(User).get(id)
    if not user:
        flask.abort(404)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    url = f'{flask.request.host_url}qr_decode/{user.id}'
    qr.add_data(url)

    t_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(t_file, format='JPEG')
    t_file.seek(0)

    return send_file(t_file.name,
                     mimetype='image/jpeg',
                     attachment_filename=t_file.name,
                     as_attachment=True
                     )


@app.route('/qr_decode/<id>')
def qr_decode(id):
    return redirect(f'{flask.request.host_url}admin/user/edit/?id={id}')


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('upload'))


@app.route('/')
def index():
    return redirect(url_for('upload'))
