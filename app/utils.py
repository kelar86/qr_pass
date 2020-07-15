import gzip
import os
import tempfile
from threading import Thread

import cv2
import flask
import qrcode
from flask import current_app
from flask_login import current_user
from qrcode.util import QRData, MODE_8BIT_BYTE
from werkzeug.local import LocalProxy

from settings import basedir


def is_face_detected(image):

    face_cascade = cv2.CascadeClassifier(os.path.join(basedir, "app/resources/haarcascade_frontalface_default.xml"))
    eye_cascade = cv2.CascadeClassifier(os.path.join(basedir, "app/resources/haarcascade_eye.xml"))

    img = cv2.imread(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    face_boxes = []
    for (x, y, w, h) in faces:
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = img[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        # if len(eyes) < 2:
        #     return []
        # for (ex, ey, ew, eh) in eyes:
        #     cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

        face_boxes.append((x, y, x + w, y + h))

    cv2.waitKey(0)
    return face_boxes


def get_qr_file(id: int, format: str) -> tempfile._TemporaryFileWrapper:

    def get_suffix(_format):
        return {
            'PNG': '.png',
            'PDF': '.pdf',
            'JPEG': '.jpg'
        }[_format.upper()]

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    url = f'{flask.request.host_url}qr_decode/{id}/'
    qr.add_data(url)
    img = qr.make_image(fill_color="black", back_color="white")
    t_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix=get_suffix(format))
    img.save(t_file, format=format)
    t_file.seek(0)
    return t_file


def threaded(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target = f, args = args, kwargs = kwargs)
        thr.start()
    return wrapper


# def owner_user(f):
#     def decorated_view(*args, **kwargs):
#         # current_user = LocalProxy(lambda: _get_user())
#         _id = args[0] if len(args)>0 else kwargs.get('id')
#         if current_user.id != _id:
#             return current_app.login_manager.unauthorized()
#         return f(*args, **kwargs)
#     return decorated_view

# .eJxTujDxwtaLDRf2XtiiAGRuuNh0sefCrgv7Lmy6sONiu8KFeUCBJjB3H1DVlgtbL-y5sBlI7gWKd4DpFiC5G6hpixIA4NE1CQ.4pc8_0yHjdpI4ykoo2SI8-JKJD0
#
# d219fc73-3da5-4c8c-b839-383597d504e3:Константин:Константинович:Оттовордемгентшенфельд:11-09-1986