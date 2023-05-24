from app import db
from sqlalchemy.dialects.mysql import SMALLINT, VARCHAR, TINYINT


class Mark(db.Model):
    id = db.Column(SMALLINT(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    name_rus = db.Column(VARCHAR(255))
    transport_type_id = db.Column(TINYINT(), db.ForeignKey('transport_type.id'))

    transport_type = db.relationship(
        'TransportType',
        backref=db.backref('marks', lazy='dynamic')
    )
