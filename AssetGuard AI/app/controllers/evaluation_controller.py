from flask import Blueprint, request

from app.models.user import UserRole
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
        location_id=location_id_i,
        asset_id=asset_id_i,
        equipment=eq_str,
        equipment_model=model_str,
        load_parameter_value=load_f,
        remark=remark_str,
    )
    return ok(data)


@evaluations_bp.get("/history")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def history():
    _ = get_auth_context()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    if page < 1 or page_size < 1 or page_size > 200:
        raise ApiError("Invalid pagination parameters", 400, code="validation_error")

    data = EvaluationService.history(page=page, page_size=page_size)
    return ok(data)
