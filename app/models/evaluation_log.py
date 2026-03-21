import enum
from datetime import datetime, timezone

from app.extensions import db


def _utc_now() -> datetime:
    """Timezone-aware UTC now (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


class EvaluationStatus(str, enum.Enum):
    """Compliance outcome."""

    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"


class EvaluationLog(db.Model):
    """Audit trail for each evaluation (who, when, asset, loads, units, remark)."""

    __tablename__ = "evaluation_logs"

    id = db.Column(db.Integer, primary_key=True)

    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False, index=True)
    asset = db.relationship("Asset", backref=db.backref("evaluation_logs", lazy=True))

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    user = db.relationship("User", backref=db.backref("evaluation_logs", lazy=True))

    # Planned load in the asset's unit (after conversion from the submitted unit)
    planned_load = db.Column(db.Float, nullable=False)
    submitted_planned_load = db.Column(db.Float, nullable=True)
    submitted_unit = db.Column(db.String(32), nullable=True)
    remark = db.Column(db.Text, nullable=True)

    status = db.Column(db.Enum(EvaluationStatus), nullable=False)
    overload_percentage = db.Column(db.Float, nullable=False, default=0.0)
    evaluated_at = db.Column(db.DateTime, nullable=False, default=_utc_now, index=True)
