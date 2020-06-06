import uuid

from app import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, \
    String, Boolean

Base = db.Model

def generate_uuid():
    return str(uuid.uuid4())


class User(Base, UserMixin):
    __tablename__ = 'user'

    id = Column('id', String, primary_key=True, default=generate_uuid())
    phone = Column('phone', String, nullable=False)
    passport_number = Column('passport_number', Integer)
    active = Column('active', Boolean, nullable=False, default=False)
    photo = Column('photo', String)

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return self.active


class Pass(Base):
    __tablename__ = 'pass'
    id = Column('id', Integer, primary_key=True)
