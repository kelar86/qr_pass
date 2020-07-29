import base64
import gzip
import os
import tempfile
from threading import Thread

import cv2
import flask
import qrcode
import treepoem
from PIL import Image
from flask import current_app
from flask_login import current_user
from qrcode.util import QRData, MODE_8BIT_BYTE
from werkzeug.local import LocalProxy

from app import signer
from settings import basedir, SIGNER_SECRET_KEY

from itsdangerous import Signer, URLSafeSerializer
import hashlib

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


def get_qr_file(id: int, format: str, barcode_type: str='datamatrix') -> tempfile._TemporaryFileWrapper:

    def get_suffix(_format):
        return {
            'PNG': '.png',
            'PDF': '.pdf',
            'JPEG': '.jpg'
        }[_format.upper()]

    url = f'{flask.request.host_url}qr/{id}/'
    t_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix=get_suffix(format))

    if  'qr_code' in barcode_type:

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_Q,
            box_size=10,
            border=4,
        )

        qr.add_data(url)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(t_file, format=format)

    if 'datamatrix' in barcode_type:

        img = treepoem.generate_barcode(
            barcode_type='datamatrix',
            data=url
        )
        img.thumbnail((450, 450), Image.ANTIALIAS)
        img.save(t_file, format=format)


    t_file.seek(0)
    return t_file


def threaded(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target = f, args = args, kwargs = kwargs)
        thr.start()
    return wrapper

def sign_data(data):
    signature = signer.get_signature(data)
    return signature

def encode_data(data):
    return base64.urlsafe_b64encode(data.encode('koi8-r')).decode()

def decode_data(data):
    return base64.b64decode(data)