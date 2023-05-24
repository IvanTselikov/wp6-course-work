from app import db
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR


class Color(db.Model):
    id = db.Column(TINYINT(), primary_key=True)
    name = db.Column(VARCHAR(100), nullable=False)
    red = db.Column(TINYINT(unsigned=True), nullable=False)
    green = db.Column(TINYINT(unsigned=True), nullable=False)
    blue = db.Column(TINYINT(unsigned=True), nullable=False)
