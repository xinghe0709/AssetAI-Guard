from datetime import datetime, timezone

from sqlalchemy import select

from app.extensions import db
from app.models import Asset, EvaluationLog, LoadCapacity
from app.models.evaluation_log import EvaluationStatus
from app.utils.equipment_mapping import normalize_capacity_name, resolve_equipment
from app.utils.errors import ApiError


def _evaluated_at_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class EvaluationService:
    @staticmethod
    def evaluate_load(
        *,
        user_id: int,
        location_id: int,
        asset_id: int,
        equipment: str,
        equipment_model: str | None,
        load_parameter_value: float,
        remark: str | None = None,
    ) -> dict:
        _, expected_metric, capacity_name_key = resolve_equipment(equipment)
        capacity_name_key = normalize_capacity_name(capacity_name_key)

        if load_parameter_value <= 0:
            raise ApiError("loadParameterValue must be greater than 0", 400, code="invalid_load_value")

        asset = Asset.query.filter_by(id=asset_id).first()
        if asset is None:
            raise ApiError("Asset not found", 404, code="asset_not_found")
        if asset.location_id != location_id:
            raise ApiError(
                "Asset does not belong to the provided locationId",
                400,
                code="asset_location_mismatch",
            )

        capacity = (
            LoadCapacity.query.filter(
                LoadCapacity.asset_id == asset_id,
                LoadCapacity.name == capacity_name_key,
            )
            .first()
        )
        if capacity is None:
            raise ApiError(
                f'Asset has no load capacity named "{capacity_name_key}" for this equipment type',
                400,
                code="capacity_not_found",
            )

        if capacity.metric.value != expected_metric:
            raise ApiError(
                f"Load capacity metric mismatch: stored {capacity.metric.value!r}, expected {expected_metric!r} for this equipment",
                400,
                code="capacity_metric_mismatch",
            )

        max_v = float(capacity.max_load)
        val = float(load_parameter_value)
        is_compliant = val <= max_v
        if is_compliant:
            status = EvaluationStatus.COMPLIANT
            overload_pct = 0.0
        else:
            status = EvaluationStatus.NON_COMPLIANT
            overload_pct = (val - max_v) / max_v if max_v > 0 else 0.0

        remark_clean = (remark or "").strip() or None
        model_clean = (equipment_model or "").strip() or None

        log = EvaluationLog(
            asset_id=asset.id,
            user_id=user_id,
            equipment=equipment,
            equipment_model=model_clean,
            load_parameter_value=val,
            load_parameter_metric=expected_metric,
            matched_capacity_name=capacity.name,
            status=status,
            overload_percentage=float(overload_pct),
            remark=remark_clean,
            evaluated_at=datetime.now(timezone.utc),
        )
        db.session.add(log)
        db.session.commit()

        return {
            "asset": {
                "id": asset.id,
                "name": asset.name,
                "locationId": asset.location_id,
            },
            "equipment": equipment,
            "equipmentModel": model_clean,
            "loadParameterValue": val,
            "loadParameterMetric": expected_metric,
            "matchedCapacityName": capacity.name.value,
            "capacityMaxLoad": max_v,
            "status": status.value,
            "overloadPercentage": float(overload_pct),
            "remark": remark_clean,
        }

    @staticmethod
    def history(*, page: int, page_size: int) -> dict:
        stmt = (
            select(EvaluationLog)
            .order_by(EvaluationLog.evaluated_at.desc(), EvaluationLog.id.desc())
        )
        pagination = db.paginate(stmt, page=page, per_page=page_size, error_out=False)
        items = [
            {
                "id": log.id,
                "assetId": log.asset_id,
                "assetName": log.asset.name if log.asset else None,
                "equipment": log.equipment,
                "equipmentModel": log.equipment_model,
                "loadParameterValue": log.load_parameter_value,
                "loadParameterMetric": log.load_parameter_metric,
                "matchedCapacityName": log.matched_capacity_name,
                "status": log.status.value,
                "overloadPercentage": log.overload_percentage,
                "remark": log.remark,
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
