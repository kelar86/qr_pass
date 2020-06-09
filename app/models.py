import uuid

from sqlalchemy.orm import relationship

from app import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, \
    String, Boolean, DateTime, ForeignKey

Base = db.Model

def generate_uuid():
    return str(uuid.uuid4())


class Person(Base, UserMixin):
    __tablename__ = 'person'

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String, nullable=False)
    passport_number = Column(Integer)
    active = Column(Boolean, nullable=False, default=False)
    photo = Column(String)

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return self.active


class Pass(Base):
    __tablename__ = 'pass'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_at = Column(DateTime)
    expire_at = Column(DateTime)
    verified = Column(Boolean, nullable=False, default=False)
    person_id = Column(ForeignKey('person.id'), nullable=False)


class Passage(Base):
    __tablename__ = 'passage'
    id = Column(Integer, primary_key=True, autoincrement=True)
