from app import db
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, SMALLINT


class Generation(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    model_id = db.Column(INTEGER(), db.ForeignKey('model.id'), nullable=False)
    year_begin = db.Column(SMALLINT())
    year_end = db.Column(SMALLINT())

    model = db.relationship('Model', backref=db.backref('generations', lazy='dynamic'))
