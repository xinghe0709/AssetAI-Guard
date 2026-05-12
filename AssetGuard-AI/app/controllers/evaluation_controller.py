from datetime import date, datetime

from flask import Blueprint, request

from app.extensions import db
from app.models import Asset, EvaluationLog, LoadCapacity
from app.models.user import UserRole
from app.services.alert_service import AlertService
from app.services.evaluation_service import EvaluationService
from app.utils.auth import get_auth_context, require_auth, require_roles
from app.utils.equipment_mapping import equipment_options
from app.utils.errors import ApiError
from app.utils.responses import ok

evaluations_bp = Blueprint("evaluations", __name__)


@evaluations_bp.get("/equipment-options")
@require_auth
def equipment_options_route():
    """Equipment types with load parameter label and metric (for dynamic form)."""
    return ok(equipment_options())


@evaluations_bp.post("/check")
@require_auth
def check():
    """
    Compare user load parameter to the asset load capacity row mapped by equipment type (PDF).

    JSON: locationId, assetId, equipment, loadParameterValue; optional equipmentModel, remark.
    """
    ctx = get_auth_context()
    body = request.get_json(silent=True) or {}

    location_id = body.get("locationId")
    asset_id = body.get("assetId")
    equipment = body.get("equipment")
    load_val = body.get("loadParameterValue")
    equipment_model = body.get("equipmentModel")
    remark = body.get("remark")

    if location_id is None or asset_id is None or equipment is None or load_val is None:
        raise ApiError(
            "locationId, assetId, equipment, and loadParameterValue are required",
            400,
            code="validation_error",
        )

    try:
        location_id_i = int(location_id)
    except (TypeError, ValueError) as e:
        raise ApiError("locationId must be an integer", 400, code="validation_error") from e

    try:
        asset_id_i = int(asset_id)
    except (TypeError, ValueError) as e:
        raise ApiError("assetId must be an integer", 400, code="validation_error") from e

    try:
        load_f = float(load_val)
    except (TypeError, ValueError) as e:
        raise ApiError("loadParameterValue must be a number", 400, code="validation_error") from e

    eq_str = str(equipment).strip()
    model_str = equipment_model if isinstance(equipment_model, str) else None
    remark_str = remark if isinstance(remark, str) else None

    data = EvaluationService.evaluate_load(
        user_id=ctx.user_id,
        user_email=ctx.email,
        location_id=location_id_i,
        asset_id=asset_id_i,
        equipment=eq_str,
        equipment_model=model_str,
        load_parameter_value=load_f,
        remark=remark_str,
    )
    return ok(data)


@evaluations_bp.post("/<int:log_id>/notify")
@require_auth
def notify(log_id: int):
    """Re-send email notification for an existing evaluation."""
    ctx = get_auth_context()
    log = EvaluationLog.query.get(log_id)
    if log is None:
        raise ApiError("Evaluation log not found", 404, code="not_found")

    asset = Asset.query.get(log.asset_id)
    if asset is None:
        raise ApiError("Asset not found", 404, code="asset_not_found")

    capacity = (
        LoadCapacity.query.filter_by(
            asset_id=log.asset_id,
            name=log.matched_capacity_name,
        ).first()
    )
    max_load = float(capacity.max_load) if capacity else 0.0

    result = AlertService.notify_non_compliant(
        asset_name=asset.name,
        status=log.status.value,
        overload_percent=float(log.overload_percentage),
        recipient_email=ctx.email,
        equipment=log.equipment,
        equipment_model=log.equipment_model,
        capacity_name=log.matched_capacity_name or "",
        capacity_max_load=max_load,
        load_parameter_value=float(log.load_parameter_value),
        load_parameter_metric=log.load_parameter_metric or "",
        force=True,
    )
    if result is not None:
        log.email_status, log.email_error = result
        db.session.commit()

    return ok({
        "emailStatus": log.email_status or "Skipped",
        "emailError": log.email_error,
    })


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ApiError(
            f"Invalid date format: {value!r}; expected YYYYY-MM-DD",
            400,
            code="validation_error",
        )


@evaluations_bp.get("/history")
@require_auth
def history():
    auth_context = get_auth_context()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    if page < 1 or page_size < 1 or page_size > 200:
        raise ApiError("Invalid pagination parameters", 400, code="validation_error")

    asset_id = request.args.get("assetId", type=int)
    equipment = request.args.get("equipment")
    status = request.args.get("status")
    from_date = _parse_optional_date(request.args.get("fromDate"))
    to_date = _parse_optional_date(request.args.get("toDate"))

    # Contractors can only view their own evaluation history
    user_id = None
    if auth_context.role == UserRole.CONTRACTORS.value:
        user_id = auth_context.user_id

    data = EvaluationService.history(
        page=page,
        page_size=page_size,
        asset_id=asset_id,
        user_id=user_id,
        equipment=equipment,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )
    return ok(data)


@evaluations_bp.get("/history/user/<int:user_id>")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def history_by_user(user_id: int):
    _ = get_auth_context()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    if page < 1 or page_size < 1 or page_size > 200:
        raise ApiError("Invalid pagination parameters", 400, code="validation_error")

    asset_id = request.args.get("assetId", type=int)
    equipment = request.args.get("equipment")
    status = request.args.get("status")
    from_date = _parse_optional_date(request.args.get("fromDate"))
    to_date = _parse_optional_date(request.args.get("toDate"))

    data = EvaluationService.history(
        page=page,
        page_size=page_size,
        asset_id=asset_id,
        user_id=user_id,
        equipment=equipment,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )
    return ok(data)


@evaluations_bp.get("/dashboard-summary")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def dashboard_summary():
    _ = get_auth_context()
    limit = int(request.args.get("limit", 10))
    if limit < 1 or limit > 100:
        raise ApiError("Invalid limit parameter", 400, code="validation_error")

    data = EvaluationService.dashboard_summary(limit=limit)
    return ok(data)
