import enum
from datetime import datetime, timezone

from app.extensions import db


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EvaluationStatus(str, enum.Enum):
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"


class EvaluationLog(db.Model):
    """User submission audit: equipment + load parameter vs matched asset load capacity."""

    __tablename__ = "evaluation_logs"

    id = db.Column(db.Integer, primary_key=True)

    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False, index=True)
    asset = db.relationship("Asset", backref=db.backref("evaluation_logs", lazy=True))

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    user = db.relationship("User", backref=db.backref("evaluation_logs", lazy=True))

    equipment = db.Column(db.String(128), nullable=False)
    equipment_model = db.Column(db.Text, nullable=True)
    load_parameter_value = db.Column(db.Float, nullable=False)
    load_parameter_metric = db.Column(db.String(32), nullable=False)
    matched_capacity_name = db.Column(db.String(128), nullable=False)

    status = db.Column(db.Enum(EvaluationStatus), nullable=False)
    overload_percentage = db.Column(db.Float, nullable=False, default=0.0)
    remark = db.Column(db.Text, nullable=True)
    evaluated_at = db.Column(db.DateTime, nullable=False, default=_utc_now, index=True)
