from app import db
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR


class Location(db.Model):
    id = db.Column(INTEGER(), primary_key=True)
    name = db.Column(VARCHAR(100), nullable=False)

    def get_id(name):
        name = name.strip().title()
        location = Location.query.filter_by(name=name).first()
        if location:
            return location.id
    
    def __init__(self, *args, **kwargs):
        super(Location, self).__init__(*args, **kwargs)
        self.name = self.name.strip().title()
