import uuid

from flask_login import UserMixin
from sqlalchemy import Column, Integer, \
    String, Boolean, ForeignKey, Date

from app import db

Base = db.Model

def generate_uuid():
    return str(uuid.uuid4())


class Person(Base, UserMixin):
    __tablename__ = 'person'

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String)
    passport_number = Column(String)
    active = Column(Boolean, nullable=False, default=False)
    photo = Column(String)
    signature = Column(String)

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return self.active


class Pass(Base):
    __tablename__ = 'pass'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_at = Column(Date)
    expire_at = Column(Date)
    verified = Column(Boolean, nullable=False, default=False)
    person_id = Column(ForeignKey('person.id'), nullable=False)


class Passage(Base):
    __tablename__ = 'passage'
    id = Column(Integer, primary_key=True, autoincrement=True)
