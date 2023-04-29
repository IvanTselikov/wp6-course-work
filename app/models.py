from app import db, login
from sqlalchemy.dialects.mysql import *
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from flask_login import UserMixin

from datetime import datetime as dt


class User(UserMixin, db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    first_name = db.Column(VARCHAR(100), nullable=False)
    last_name = db.Column(VARCHAR(100), nullable=False)
    patronymic = db.Column(VARCHAR(100))
    login = db.Column(VARCHAR(20), index=True, unique=True, nullable=False)
    password_hash = db.Column(VARCHAR(255), nullable=False)
    email = db.Column(VARCHAR(320), index=True, unique=True)
    phone_number = db.Column(VARCHAR(20), nullable=False)
    registration_date = db.Column(DATETIME(), nullable=False, default=dt.utcnow)
    photo = db.Column(BLOB())
    is_admin = db.Column(TINYINT(1), nullable=False)
    location_id = db.Column(INTEGER(), db.ForeignKey('location.id'))

    ads = db.relationship('Ad', backref='seller', lazy='dynamic')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_location(self, name):
        self.location_id = Location.get_id_by_name(name)

    def get_chats(self):
        pass

    def get_chat_messages(self, user_id):
        pass

    def __repr__(self):
        return '<User {}>'.format(self.login)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Message(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    sender_id = db.Column(INTEGER(), db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(INTEGER(), db.ForeignKey('user.id'), nullable=False)
    text = db.Column(TEXT(), nullable=False)
    sent_at = db.Column(DATETIME(), nullable=False, default=dt.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])


class Ad(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    car_id = db.Column(INTEGER(), db.ForeignKey('modification.id'), nullable=False)
    release_year = db.Column(SMALLINT(), nullable=False)
    vin = db.Column(CHAR(17), nullable=False)
    license_plate_number = db.Column(VARCHAR(20))
    pts_type_id = db.Column(TINYINT(), db.ForeignKey('pts_type.id'), nullable=False)
    owners_count = db.Column(TINYINT(), nullable=False)
    color_id = db.Column(TINYINT(), db.ForeignKey('color.id'))
    is_broken = db.Column(TINYINT(1), nullable=False)
    mileage = db.Column(INTEGER(), nullable=False)
    seller_id = db.Column(INTEGER(), db.ForeignKey('user.id'), nullable=False)
    location_id = db.Column(INTEGER(), db.ForeignKey('location.id'), nullable=False)
    price = db.Column(INTEGER(), nullable=False)
    description = db.Column(TEXT())

    photos = db.relationship('AdPhoto', backref='ad', lazy='dynamic')


class Location(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(100), nullable=False)

    users = db.relationship('User', backref='location', lazy='dynamic')
    ads = db.relationship('Ad', backref='location', lazy='dynamic')

    def get_id_by_name(name):
        name = name.strip().title()
        location = Location.query.filter_by(name=name).first()
        if location:
            return location.id
        new_location = Location(name=name)
        db.session.add(new_location)
        db.session.commit()
        return new_location.id


class AdPhoto(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    ad_id = db.Column(INTEGER(), db.ForeignKey('ad.id'), nullable=False)
    photo = db.Column(BLOB(), nullable=False)
    is_main = db.Column(TINYINT(1), nullable=False)


class AdStatus(db.Model):
    id = db.Column(TINYINT(), primary_key=True)
    name = db.Column(VARCHAR(100), nullable=False)


class StatusChange(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    status_id = db.Column(TINYINT(), db.ForeignKey('ad_status.id'), nullable=False)
    ad_id = db.Column(INTEGER(), db.ForeignKey('ad.id'), nullable=False)
    admin_id = db.Column(INTEGER(), db.ForeignKey('user.id'), nullable=False)
    set_at = db.Column(DATETIME(), nullable=False, default=dt.utcnow)


class PtsType(db.Model):
    id = db.Column(TINYINT(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)


class Color(db.Model):
    id = db.Column(TINYINT(), primary_key=True)
    name = db.Column(VARCHAR(100), nullable=False)
    red = db.Column(TINYINT(unsigned=True), nullable=False)
    green = db.Column(TINYINT(unsigned=True), nullable=False)
    blue = db.Column(TINYINT(unsigned=True), nullable=False)


class TransportType(db.Model):
    id = db.Column(TINYINT(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)


class Mark(db.Model):
    id = db.Column(SMALLINT(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    transport_type_id = db.Column(TINYINT(), db.ForeignKey('transport_type.id'))


class Model(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    mark_id = db.Column(SMALLINT(), db.ForeignKey('mark.id'), nullable=False)


class Generation(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    model_id = db.Column(INTEGER(), db.ForeignKey('model.id'), nullable=False)
    year_begin = db.Column(SMALLINT())
    year_end = db.Column(SMALLINT())


class Serie(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    generation_id = db.Column(INTEGER(), db.ForeignKey('generation.id'), nullable=False)


class Modification(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    serie_id = db.Column(INTEGER(), db.ForeignKey('serie.id'), nullable=False)


class Characteristic(db.Model):
    id = db.Column(SMALLINT(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    parent_id = db.Column(SMALLINT(), db.ForeignKey('characteristic.id'))


class CharacteristicValue(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    value = db.Column(VARCHAR(255), nullable=False)
    unit = db.Column(VARCHAR(255))
    characteristic_id = db.Column(SMALLINT(), db.ForeignKey('characteristic.id'), nullable=False)
    modification_id = db.Column(INTEGER(), db.ForeignKey('modification.id'), nullable=False)
