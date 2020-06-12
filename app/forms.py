import os
import tempfile

import phonenumbers
from PIL import Image, ImageDraw

from app import photos, uuid
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms.fields.html5 import TelField, IntegerField
from app.utils import is_face_detected
from settings import basedir


class LoginForm(FlaskForm):
    phone = TelField('Номер телефона:', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня', default=True)
    submit = SubmitField('Войти')

    def validate_phone(self, field):

        cleaned_data = field.data.replace("+", '').replace("-", '').replace('_', '')

        if len(cleaned_data) != 11:
            raise ValidationError('Номер телефона должен содержать 11 цифр')

        input_number = phonenumbers.parse(field.data)
        if not (phonenumbers.is_valid_number(input_number)):
            raise ValidationError('Не верный номер!')



class UploadForm(FlaskForm):
    photo = FileField('Фотография', validators=[FileAllowed(photos, u'Image only!'), FileRequired(u'File was empty!')])
    submit = SubmitField('Загрузить')
    detected_face = None
    tempname = str(uuid.uuid4())

    # def validate_photo(self, photo):
    #     with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as t_file:
    #         with Image.open(photo.data) as img:
    #             img.save(t_file, format='PNG')
    #             self.detected_face = is_face_detected(t_file.name)
    #             if not self.detected_face:
    #                 raise ValidationError('Лицо на фотографии не обнаружено или не читаемо. Загрузите другое фото!')

                # draw = ImageDraw.Draw(img)
                # first = self.detected_face[0]
                # draw.rectangle(first)
                #
                # img.save(os.path.join(basedir, f'app/static/{self.tempname}') + '.png', format='PNG')

    # with ima


class PassportForm(FlaskForm):
    passport_number = IntegerField('Номер паспорта', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Изменить')
