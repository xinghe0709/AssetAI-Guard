from app.extensions import db


class Asset(db.Model):
    """Berth / equipment site asset; belongs to a Location (PDF)."""

    __tablename__ = "assets"
    __table_args__ = (
        db.UniqueConstraint("location_id", "name", name="uq_asset_location_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)

    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)
    location = db.relationship("Location", backref=db.backref("assets", lazy=True))
