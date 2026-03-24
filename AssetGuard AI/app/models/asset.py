from app.extensions import db


class Asset(db.Model):
    """Berth / equipment site asset; belongs to a Location (PDF)."""

    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)
    company = db.relationship("Company", backref=db.backref("assets", lazy=True))

    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)
    location = db.relationship("Location", backref=db.backref("assets", lazy=True))
