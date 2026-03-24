from app.extensions import db


class Company(db.Model):
    """Tenant root: users and assets are scoped by company_id."""

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
