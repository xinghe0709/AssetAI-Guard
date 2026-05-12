from datetime import date, datetime, timezone

from sqlalchemy import select

from app.extensions import db
from app.models import Asset, EvaluationLog, LoadCapacity
from app.models.evaluation_log import EvaluationStatus
from app.utils.equipment_mapping import normalize_capacity_name, resolve_equipment
from app.utils.errors import ApiError


def _evaluated_at_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone().replace(microsecond=0).isoformat()


class EvaluationService:
    @staticmethod
    def evaluate_load(
        *,
        user_id: int,
        user_email: str,
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
            "id": log.id,
            "emailStatus": log.email_status,
            "emailError": log.email_error,
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
    def history(
        *,
        page: int,
        page_size: int,
        asset_id: int | None = None,
        user_id: int | None = None,
        equipment: str | None = None,
        status: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict:
        stmt = select(EvaluationLog)

        if asset_id is not None:
            stmt = stmt.where(EvaluationLog.asset_id == asset_id)
        if user_id is not None:
            stmt = stmt.where(EvaluationLog.user_id == user_id)
        if equipment is not None:
            stmt = stmt.where(EvaluationLog.equipment == equipment)
        if status is not None:
            try:
                status_enum = EvaluationStatus(status)
            except ValueError:
                raise ApiError(
                    f"Invalid status value; allowed: {[s.value for s in EvaluationStatus]}",
                    400,
                    code="validation_error",
                )
            stmt = stmt.where(EvaluationLog.status == status_enum)
        if from_date is not None:
            stmt = stmt.where(EvaluationLog.evaluated_at >= from_date)
        if to_date is not None:
            stmt = stmt.where(EvaluationLog.evaluated_at < to_date)

        stmt = stmt.order_by(EvaluationLog.evaluated_at.desc(), EvaluationLog.id.desc())
        pagination = db.paginate(stmt, page=page, per_page=page_size, error_out=False)
        items = []
        for log in pagination.items:
            # Query the LoadCapacity to get the max_load value
            capacity = (
                LoadCapacity.query.filter_by(
                    asset_id=log.asset_id,
                    name=log.matched_capacity_name,
                ).first()
            )
            # Format with thousands separator
            if capacity:
                capacity_max_load = f"{int(capacity.max_load):,}{log.load_parameter_metric}"
            else:
                capacity_max_load = "-"
            load_planned = f"{int(log.load_parameter_value):,}{log.load_parameter_metric}"
            
            items.append({
                "id": log.id,
                "assetId": log.asset_id,
                "assetName": log.asset.name if log.asset else None,
                "equipment": log.equipment,
                "equipmentModel": log.equipment_model,
                "loadParameterValue": log.load_parameter_value,
                "loadParameterMetric": log.load_parameter_metric,
                "matchedCapacityName": log.matched_capacity_name,
                "capacityMaxLoad": capacity.max_load if capacity else None,
                "capacityMetric": log.load_parameter_metric,
                "capacityMaxLoadDisplay": f"{capacity_max_load} / {load_planned}",
                "status": log.status.value,
                "overloadPercentage": log.overload_percentage,
                "remark": log.remark,
                "evaluatedAt": _evaluated_at_iso(log.evaluated_at),
                "userId": log.user_id,
                "userEmail": log.user.email if log.user else None,
            })
        return {
            "items": items,
            "page": pagination.page,
            "pageSize": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }

    @staticmethod
    def dashboard_summary(*, limit: int = 10) -> dict:
        logs: list[EvaluationLog] = (
            EvaluationLog.query.order_by(EvaluationLog.evaluated_at.desc(), EvaluationLog.id.desc()).all()
        )

        total = len(logs)
        compliant_count = sum(1 for log in logs if log.status == EvaluationStatus.COMPLIANT)
        non_compliant_count = total - compliant_count
        compliance_rate = round((compliant_count / total) * 100, 2) if total else 0.0

        overload_logs = [log for log in logs if log.status == EvaluationStatus.NON_COMPLIANT]
        avg_overload_percentage = (
            round((sum(log.overload_percentage for log in overload_logs) / len(overload_logs)) * 100, 2)
            if overload_logs
            else 0.0
        )
        max_overload_percentage = (
            round(max(log.overload_percentage for log in overload_logs) * 100, 2) if overload_logs else 0.0
        )

        equipment_breakdown: dict[str, int] = {}
        asset_breakdown: dict[str, int] = {}
        for log in logs:
            equipment_breakdown[log.equipment] = equipment_breakdown.get(log.equipment, 0) + 1
            asset_name = log.asset.name if log.asset else f"Asset #{log.asset_id}"
            asset_breakdown[asset_name] = asset_breakdown.get(asset_name, 0) + 1

        top_assets = [
            {"assetName": name, "evaluationCount": count}
            for name, count in sorted(asset_breakdown.items(), key=lambda item: item[1], reverse=True)[:limit]
        ]
        equipment_stats = [
            {"equipment": equipment, "evaluationCount": count}
            for equipment, count in sorted(equipment_breakdown.items(), key=lambda item: item[1], reverse=True)
        ]

        recent_evaluations = [
            {
                "id": log.id,
                "assetName": log.asset.name if log.asset else None,
                "equipment": log.equipment,
                "status": log.status.value,
                "loadParameterValue": log.load_parameter_value,
                "loadParameterMetric": log.load_parameter_metric,
                "overloadPercentage": round(log.overload_percentage * 100, 2),
                "evaluatedAt": _evaluated_at_iso(log.evaluated_at),
            }
            for log in logs[:limit]
        ]

        return {
            "totals": {
                "evaluations": total,
                "compliant": compliant_count,
                "nonCompliant": non_compliant_count,
                "complianceRatePercentage": compliance_rate,
            },
            "overloadStats": {
                "averageOverloadPercentage": avg_overload_percentage,
                "maxOverloadPercentage": max_overload_percentage,
            },
            "equipmentStats": equipment_stats,
            "topAssets": top_assets,
            "recentEvaluations": recent_evaluations,
        }
