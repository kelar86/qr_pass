from app import app, db
from app.models import Person
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

admin = Admin(app, name='qr_pass_admin', template_mode='bootstrap3')


class BaseView(ModelView):
    form_excluded_columns = ['active', 'photo']

    column_labels = {
        'phone': 'Телефон',
        'passport_number': 'Номер паспорта',
        'photo': 'Фотографи'
    }
    can_delete = False
    can_create = False


admin.add_view(BaseView(Person, db.session))
