from app import db
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR


class PtsType(db.Model):
    id = db.Column(TINYINT(), primary_key=True)
    name = db.Column(VARCHAR(255), nullable=False)
