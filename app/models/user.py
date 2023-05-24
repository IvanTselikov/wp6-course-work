from app import db, login
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, DATETIME, TINYINT
from werkzeug.security import generate_password_hash, check_password_hash
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
    is_admin = db.Column(TINYINT(1), nullable=False)
    location_id = db.Column(INTEGER(), db.ForeignKey('location.id'))

    location = db.relationship('Location', backref=db.backref('users', lazy='dynamic'))

    def __init__(self, password, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.set_password(password)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_recommended_ads(self):
        if self.location:
            return self.location.ads
        return None

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
