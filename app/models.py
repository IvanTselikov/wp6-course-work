from app import db, login
from sqlalchemy.dialects.mysql import *
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from flask_login import UserMixin
from sqlalchemy import or_, and_, not_

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
    is_admin = db.Column(TINYINT(1), nullable=False)
    location_id = db.Column(INTEGER(), db.ForeignKey('location.id'))

    location = db.relationship('Location', backref=db.backref('users', lazy='dynamic'))

    def __init__(self, password, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.password_hash = generate_password_hash(password)
        self.gg = 'gg'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_recommended_ads(self):
        if self.location:
            return self.location.ads
        return None
    
    def __repr__(self):
        return '<User {}>'.format(self.login)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Ad(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    car_id = db.Column(INTEGER(), db.ForeignKey('modification.id'), nullable=False)
    release_year = db.Column(SMALLINT(), nullable=False)
    vin = db.Column(CHAR(17), nullable=False)
    pts_type_id = db.Column(TINYINT(), db.ForeignKey('pts_type.id'), nullable=False)
    owners_count = db.Column(TINYINT(), nullable=False)
    color_id = db.Column(TINYINT(), db.ForeignKey('color.id'))
    is_broken = db.Column(TINYINT(1), nullable=False)
    mileage = db.Column(INTEGER(), nullable=False)
    seller_id = db.Column(INTEGER(), db.ForeignKey('user.id'), nullable=False)    
    location_id = db.Column(INTEGER(), db.ForeignKey('location.id'))
    price = db.Column(INTEGER(), nullable=False)
    description = db.Column(TEXT(), nullable=False, default=dt.utcnow)
    admin_id = db.Column(INTEGER(), db.ForeignKey('user.id'))
    status_id = db.Column(TINYINT(), db.ForeignKey('ad_status.id'), nullable=False, default=3)
    admin_message = db.Column(TEXT())
    updated_at = db.Column(DATETIME(), nullable=False, default=dt.utcnow)

    car = db.relationship('Modification', backref=db.backref('ads', lazy='dynamic'))
    seller = db.relationship('User', backref=db.backref('ads', lazy='dynamic'), foreign_keys=[seller_id])
    admin = db.relationship('User', backref=db.backref('moderated_ads', lazy='dynamic'), foreign_keys=[admin_id])
    location = db.relationship('Location', backref=db.backref('ads', lazy='dynamic'), order_by=updated_at)
    status = db.relationship('AdStatus', backref=db.backref('ads', lazy='dynamic'))
    color = db.relationship('Color', backref=db.backref('ads', lazy='dynamic'))
    pts_type = db.relationship('PtsType', backref=db.backref('ads', lazy='dynamic'))

    def __init__(self, *args, **kwargs):
        super(Ad, self).__init__(*args, **kwargs)
    
    def assign_admin(self):
        # администратор назначается на объявление случайным образом
        self.admin_id = User.query.filter(
            and_(User.is_admin == 1, not_(User.id == self.admin_id))
        ).order_by(func.rand()).first().id

    def updated_ago(self):
        delta = dt.utcnow() - self.updated_at

        time_parts = [
            {'name': 'нед', 'duration': 60*60*24*7},
            {'name': 'д', 'duration': 60*60*24},
            {'name': 'ч', 'duration': 60*60},
            {'name': 'мин', 'duration': 60},
            {'name': 'сек', 'duration': 1}
        ]

        seconds = int(delta.total_seconds())

        for part in time_parts:
            count = seconds // part['duration']
            if count:
                return '{} {} назад'.format(count, part['name'])

        return 'только что'


class Location(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(100), nullable=False)

    def get_id(name):
        name = name.strip().title()
        location = Location.query.filter_by(name=name).first()
        if location:
            return location.id
    
    def __init__(self, *args, **kwargs):
        super(Location, self).__init__(*args, **kwargs)
        self.name = self.name.strip().title()


class AdStatus(db.Model):
    id = db.Column(TINYINT(), primary_key=True)
    name = db.Column(VARCHAR(100), nullable=False)


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

    transport_type = db.relationship('TransportType', backref=db.backref('marks', lazy='dynamic'))


class Model(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    mark_id = db.Column(SMALLINT(), db.ForeignKey('mark.id'), nullable=False)

    mark = db.relationship('Mark', backref=db.backref('models', lazy='dynamic'))


class Generation(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    model_id = db.Column(INTEGER(), db.ForeignKey('model.id'), nullable=False)
    year_begin = db.Column(SMALLINT())
    year_end = db.Column(SMALLINT())

    model = db.relationship('Model', backref=db.backref('generations', lazy='dynamic'))


class Serie(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    generation_id = db.Column(INTEGER(), db.ForeignKey('generation.id'), nullable=False)

    generation = db.relationship('Generation', backref=db.backref('series', lazy='dynamic'))


class Modification(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    serie_id = db.Column(INTEGER(), db.ForeignKey('serie.id'), nullable=False)

    serie = db.relationship('Serie', backref=db.backref('modifications', lazy='dynamic'))
    characteristics = db.relationship('CharacteristicValue', backref='modification')
    
    def get_characteristic_value(self, name):
        name = name.strip().lower()
        value = list(
            filter(
                lambda ch: ch.characteristic.name.lower() == name,
                self.characteristics
            )
        )

        if value:
            return value[0].value
        return ''


class Characteristic(db.Model):
    id = db.Column(SMALLINT(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    parent_id = db.Column(SMALLINT(), db.ForeignKey('characteristic.id'))

    parent = db.relationship(
        'Characteristic',
        backref=db.backref('children', lazy='dynamic'),
        remote_side=[id]
    )


class CharacteristicValue(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    value = db.Column(VARCHAR(255), nullable=False)
    unit = db.Column(VARCHAR(255))
    characteristic_id = db.Column(SMALLINT(), db.ForeignKey('characteristic.id'), nullable=False)
    modification_id = db.Column(INTEGER(), db.ForeignKey('modification.id'), nullable=False)

    characteristic = db.relationship('Characteristic', backref=db.backref('values', lazy='dynamic'))
