from app import db
from sqlalchemy.dialects.mysql import INTEGER, SMALLINT, TINYINT, CHAR, TEXT, DATETIME
from sqlalchemy.sql import func

from datetime import datetime as dt

from .functions import format_updated_at
from .user import User
from .ad_status import AdStatus


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
    status_id = db.Column(
        TINYINT(), db.ForeignKey('ad_status.id'), nullable=False, default=AdStatus.ON_CHECKING
    )
    admin_message = db.Column(TEXT())
    updated_at = db.Column(DATETIME(), nullable=False, default=dt.utcnow)

    car = db.relationship(
        'Modification',
        backref=db.backref('ads', lazy='dynamic')
    )

    seller = db.relationship(
        'User',
        backref=db.backref('ads', lazy='dynamic'),
        foreign_keys=[seller_id]
    )

    admin = db.relationship(
        'User',
        backref=db.backref('moderated_ads', lazy='dynamic'),
        foreign_keys=[admin_id]
    )

    location = db.relationship(
        'Location',
        backref=db.backref('ads', lazy='dynamic'),
        order_by=updated_at
    )

    status = db.relationship(
        'AdStatus',
        backref=db.backref('ads', lazy='dynamic')
    )

    color = db.relationship(
        'Color',
        backref=db.backref('ads', lazy='dynamic')
    )

    pts_type = db.relationship(
        'PtsType',
        backref=db.backref('ads', lazy='dynamic')
    )
    
    def updated_ago(self):
        return format_updated_at(self.updated_at)
    
    def assign_admin(self, admin_id=None):
        if admin_id:
            self.admin_id = admin_id
        else:
            # администратор назначается на объявление случайным образом
            # (объявления администратора не проходят модерацию)
            self.admin_id = User.query.filter_by(is_admin=1)\
                .order_by(func.rand()).first().id
    
    def change_status(self, user_id, status_id, admin_message=None):
        user = User.query.get(user_id)

        if user:
            if status_id == AdStatus.OPENED:
                if user_id == self.admin_id and self.status_id in \
                    [AdStatus.ON_CHECKING, AdStatus.ON_REVISION, AdStatus.BLOCKED]:
                    # разрешить публикацию объявления (администратор)
                    self.status_id = status_id
                    self.admin_message = admin_message
                    return True
                elif user_id == self.seller_id and self.status_id == AdStatus.CLOSED:
                    # открыть закрытое объявление (владелец)
                    self.status_id = status_id
                    return True
            elif status_id == AdStatus.CLOSED and self.status_id == AdStatus.OPENED \
                and user_id == self.seller_id:
                # закрыть открытое объявление (владелец)
                self.status_id = status_id
                return True
            elif status_id == AdStatus.ON_REVISION and user_id == self.admin_id:
                # отравить на доработку (администратор)
                self.status_id = status_id
                self.admin_message = admin_message
                return True
            elif status_id == AdStatus.BLOCKED and user_id == self.admin_id and \
                self.status_id != AdStatus.BLOCKED:
                # заблокировать объявление (администратор)
                self.status_id = status_id
                self.admin_message = admin_message
                return True

        return False
