from app import db
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, SMALLINT


class Model(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    name_rus = db.Column(VARCHAR(255))
    mark_id = db.Column(SMALLINT(), db.ForeignKey('mark.id'), nullable=False)

    mark = db.relationship('Mark', backref=db.backref('models', lazy='dynamic'))
