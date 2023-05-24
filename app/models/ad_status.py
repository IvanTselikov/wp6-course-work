from app import db
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR


class AdStatus(db.Model):
    OPENED = 1
    CLOSED = 2
    ON_CHECKING = 3
    ON_REVISION = 4
    BLOCKED = 5

    id = db.Column(TINYINT(), primary_key=True)
    name = db.Column(VARCHAR(100), nullable=False)
