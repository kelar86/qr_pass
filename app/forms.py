import os
import re
import tempfile

import phonenumbers
from PIL import Image, ImageDraw

from app import photos, uuid
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms.fields.html5 import TelField, IntegerField, EmailField
from wtforms.fields.html5 import DateField as _DateField
# from wtforms.fields import DateField
from app.utils import is_face_detected
from settings import basedir


class LoginForm(FlaskForm):
    phone = TelField('Номер телефона:')
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
    temp_name = None

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


class PassportForm(FlaskForm):
    name = StringField('ФИО')
    passport_number = StringField('Паспорт')
    submit = SubmitField('Изменить номер паспорта')

    def validate_passport_number(self, field):
        cleaned_data = field.data.replace("№", '').replace(" ", '')
        if len(cleaned_data) == 0:
            raise ValidationError('Поле не может быть пустым')

        if len(cleaned_data) != 10:
            raise ValidationError('Номер паспорта (включая серию) должен содержать 10 цифр')


class CodeForm(FlaskForm):
    code = StringField(validators=[DataRequired(message="Введите код"), Length(min=4, max=4)])
    submit = SubmitField('Войти')

    def validate_code(self, field):
        cleaned_data = field.data.replace('_', '')

        if len(cleaned_data) == 0:
            raise ValidationError('Обязательное поле')

        if re.findall(r'\D', cleaned_data):
            raise ValidationError('Код должен содержать только цифры')

        if len(cleaned_data) != 4:
            raise ValidationError('Код должен содержать 4 цифры')


class EmailForm(FlaskForm):
    email = EmailField('Отправить на email', validators=[DataRequired(message="Введите email")])
    submit = SubmitField('Отправить на email')


class PassVerifyForm(FlaskForm):
    expire_at = _DateField('Срок действия пропуска:')
