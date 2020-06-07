import phonenumbers

from app import photos
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms.fields.html5 import TelField



class LoginForm(FlaskForm):
    phone = TelField('Номер телефона:', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня', default=True)
    submit = SubmitField('Войти')

    def validate_phone(form, field):

        cleaned_data = field.data.replace("+", '').replace("-", '').replace('_', '')

        if len(cleaned_data) != 11:
            raise ValidationError('Номер телефона должен содержать 11 цифр')

        input_number = phonenumbers.parse(field.data)
        if not (phonenumbers.is_valid_number(input_number)):
            raise ValidationError('Не верный номер!')



class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, u'Image only!'), FileRequired(u'File was empty!')])
    submit = SubmitField(u'Upload')
