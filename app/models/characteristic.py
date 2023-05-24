from app import db
from sqlalchemy.dialects.mysql import SMALLINT, VARCHAR


class Characteristic(db.Model):
    id = db.Column(SMALLINT(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    parent_id = db.Column(SMALLINT(), db.ForeignKey('characteristic.id'))

    parent = db.relationship(
        'Characteristic',
        backref=db.backref('children', lazy='dynamic'),
        remote_side=[id]
    )
