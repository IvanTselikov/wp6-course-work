from app import db
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, SMALLINT


class CharacteristicValue(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    value = db.Column(VARCHAR(255), nullable=False)
    unit = db.Column(VARCHAR(255))
    characteristic_id = db.Column(SMALLINT(), db.ForeignKey('characteristic.id'), nullable=False)
    modification_id = db.Column(INTEGER(), db.ForeignKey('modification.id'), nullable=False)

    characteristic = db.relationship(
        'Characteristic',
        backref=db.backref('values', lazy='dynamic')
    )
