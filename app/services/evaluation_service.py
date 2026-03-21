from datetime import datetime, timezone

from sqlalchemy import select

from app.extensions import db
from app.models import Asset, EvaluationLog
from app.models.evaluation_log import EvaluationStatus
from app.utils.errors import ApiError
from app.utils.load_units import normalize_load_unit, value_from_kg, value_to_kg


def _evaluated_at_iso(dt: datetime) -> str:
    """UTC ISO string for API responses; supports legacy naive UTC rows in the DB."""
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class EvaluationService:
    @staticmethod
    def evaluate_load(
        *,
        company_id: int,
        user_id: int,
        asset_id: int,
        planned_load: float,
        evaluation_unit: str,
        remark: str | None = None,
    ) -> dict:
        """
        Load compliance check (planned load vs asset max capacity).

        - company_id / user_id come from the token (tenant + audit).
        - planned_load is in evaluation_unit (English: kg, ton, lb).
        - Compare in kg, then persist planned_load in the asset's unit.
        - Optional remark is stored on EvaluationLog for audit.
        """
        if planned_load <= 0:
            raise ApiError("plannedLoad must be greater than 0", 400, code="invalid_planned_load")

        try:
            eval_unit_canon = normalize_load_unit(evaluation_unit)
        except ValueError as e:
            raise ApiError(str(e), 400, code="invalid_evaluation_unit") from e

        asset = Asset.query.filter_by(id=asset_id, company_id=company_id).first()
        if asset is None:
            raise ApiError("Asset not found or access denied", 404, code="asset_not_found")

        asset_unit_raw = (asset.unit or "").strip() or "kg"
        try:
            asset_unit_canon = normalize_load_unit(asset_unit_raw)
        except ValueError as e:
            raise ApiError(
                f"Asset unit is invalid: {asset.unit!r}. Use English only: kg, ton (or t), or lb.",
                400,
                code="invalid_asset_unit",
            ) from e

        try:
            planned_kg = value_to_kg(planned_load, eval_unit_canon)
            max_kg = value_to_kg(asset.max_load_capacity, asset_unit_canon)
        except ValueError as e:
            raise ApiError(str(e), 400, code="unit_conversion_error") from e

        planned_in_asset_unit = value_from_kg(planned_kg, asset_unit_canon)

        is_compliant = planned_kg <= max_kg
        if is_compliant:
            status = EvaluationStatus.COMPLIANT
            overload_pct = 0.0
        else:
            status = EvaluationStatus.NON_COMPLIANT
            overload_pct = (planned_in_asset_unit - asset.max_load_capacity) / asset.max_load_capacity

        remark_clean = (remark or "").strip() or None

        log = EvaluationLog(
            asset_id=asset.id,
            user_id=user_id,
            planned_load=planned_in_asset_unit,
            submitted_planned_load=float(planned_load),
            submitted_unit=eval_unit_canon,
            remark=remark_clean,
            status=status,
            overload_percentage=float(overload_pct),
            evaluated_at=datetime.now(timezone.utc),
        )
        db.session.add(log)
        db.session.commit()

        return {
            "asset": {
                "id": asset.id,
                "assetName": asset.asset_name,
                "maxLoadCapacity": asset.max_load_capacity,
                "unit": asset.unit,
                "normalizedUnit": asset_unit_canon,
            },
            "plannedLoad": planned_in_asset_unit,
            "submittedPlannedLoad": float(planned_load),
            "evaluationUnit": eval_unit_canon,
            "remark": remark_clean,
            "status": status.value,
            "overloadPercentage": float(overload_pct),
        }

    @staticmethod
    def history(*, company_id: int, user_id: int, page: int, page_size: int) -> dict:
        """Paginated evaluation history for the current user within the tenant."""
        stmt = (
            select(EvaluationLog)
            .join(Asset, EvaluationLog.asset_id == Asset.id)
            .where(EvaluationLog.user_id == user_id, Asset.company_id == company_id)
            .order_by(EvaluationLog.evaluated_at.desc(), EvaluationLog.id.desc())
        )

        pagination = db.paginate(stmt, page=page, per_page=page_size, error_out=False)
        items = [
            {
                "id": log.id,
                "assetId": log.asset_id,
                "assetName": log.asset.asset_name if log.asset else None,
                "plannedLoad": log.planned_load,
                "submittedPlannedLoad": log.submitted_planned_load,
                "submittedUnit": log.submitted_unit,
                "remark": log.remark,
                "status": log.status.value,
                "overloadPercentage": log.overload_percentage,
                "evaluatedAt": _evaluated_at_iso(log.evaluated_at),
            }
            for log in pagination.items
        ]

        return {
            "items": items,
            "page": pagination.page,
            "pageSize": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
