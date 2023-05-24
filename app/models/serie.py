from app import db
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR


class Serie(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
    generation_id = db.Column(INTEGER(), db.ForeignKey('generation.id'), nullable=False)

    generation = db.relationship(
        'Generation',
        backref=db.backref('series', lazy='dynamic')
    )
