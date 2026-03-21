from app.extensions import db


class Asset(db.Model):
    """
    Asset record for load compliance.

    max_load_capacity is interpreted in the unit stored in `unit` (English only: kg, ton, lb).
    """

    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    asset_name = db.Column(db.String(255), nullable=False, index=True)
    equipment_type = db.Column(db.String(255), nullable=True, index=True)
    max_load_capacity = db.Column(db.Float, nullable=False)
    source_file = db.Column(db.String(512), nullable=True)
    unit = db.Column(db.String(32), nullable=True, default="kg")

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)
    company = db.relationship("Company", backref=db.backref("assets", lazy=True))
