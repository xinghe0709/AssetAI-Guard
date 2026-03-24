from app.extensions import db


class Location(db.Model):
    """Global site (e.g. port). Shared across tenant assets."""

    __tablename__ = "locations"
    __table_args__ = (db.UniqueConstraint("name", name="uq_location_name"),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
