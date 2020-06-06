from app import photos
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    phone = StringField('email', validators=[DataRequired(), Length(min=11, max=12)])
    remember = BooleanField('remember_me', default=False)
    submit = SubmitField('login')

    # def validate_phone(form, field):
    #     if len(field.data) > 16:
    #         raise ValidationError('Invalid phone number.')
    #     try:
    #         input_number = phonenumbers.parse(field.data)
    #         if not (phonenumbers.is_valid_number(input_number)):
    #             raise ValidationError('Invalid phone number.')
    #     except:
    #         input_number = phonenumbers.parse("+1"+field.data)
    #         if not (phonenumbers.is_valid_number(input_number)):
    #             raise ValidationError('Invalid phone number.')


class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, u'Image only!'), FileRequired(u'File was empty!')])
    submit = SubmitField(u'Upload')
