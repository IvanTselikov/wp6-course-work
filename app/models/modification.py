from app import db
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR


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
