from enum import Enum

from app.extensions import db


class CapacityName(str, Enum):
    MAX_POINT_LOAD = "max point load"
    MAX_AXLE_LOAD = "max axle load"
    MAX_UNIFORM_DISTRIBUTOR_LOAD = "max uniform distributor load"
    MAX_DISPLACEMENT_SIZE = "max displacement size"


class CapacityMetric(str, Enum):
    KN = "kN"
    T = "t"
    KPA = "kPa"


class LoadCapacity(db.Model):
    """Threshold row for an asset (name + metric + max load), per client PDF."""

    __tablename__ = "load_capacities"
    __table_args__ = (
        db.UniqueConstraint("asset_id", "name", name="uq_capacity_asset_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False, index=True)
    asset = db.relationship("Asset", backref=db.backref("load_capacities", lazy=True))

    name = db.Column(
        db.Enum(
            CapacityName,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
            validate_strings=True,
            name="capacityname",
        ),
        nullable=False,
    )
    metric = db.Column(
        db.Enum(
            CapacityMetric,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
            validate_strings=True,
            name="capacitymetric",
        ),
        nullable=False,
    )
    max_load = db.Column(db.Float, nullable=False)
    details = db.Column(db.Text, nullable=True)
