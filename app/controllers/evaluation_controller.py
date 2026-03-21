from flask import Blueprint, request

from app.services.evaluation_service import EvaluationService
from app.utils.auth import get_auth_context, require_auth
from app.utils.errors import ApiError
from app.utils.responses import ok

evaluations_bp = Blueprint("evaluations", __name__)


@evaluations_bp.post("/check")
@require_auth
def check():
    """
    Evaluate planned load against asset capacity; writes an audit log row.

    JSON: assetId, plannedLoad, evaluationUnit (required, English: kg, ton/t, lb); remark (optional).
    """
    ctx = get_auth_context()
    body = request.get_json(silent=True) or {}

    asset_id = body.get("assetId")
    planned_load = body.get("plannedLoad")
    evaluation_unit = body.get("evaluationUnit")
    remark = body.get("remark")
    if asset_id is None or planned_load is None or evaluation_unit is None:
        raise ApiError("assetId, plannedLoad, and evaluationUnit are required", 400, code="validation_error")

    try:
        asset_id_i = int(asset_id)
    except (TypeError, ValueError) as e:
        raise ApiError("assetId must be an integer", 400, code="validation_error") from e

    try:
        planned_load_f = float(planned_load)
    except (TypeError, ValueError) as e:
        raise ApiError("plannedLoad must be a number", 400, code="validation_error") from e

    remark_str = remark if isinstance(remark, str) else None

    data = EvaluationService.evaluate_load(
        company_id=ctx.company_id,
        user_id=ctx.user_id,
        asset_id=asset_id_i,
        planned_load=planned_load_f,
        evaluation_unit=str(evaluation_unit).strip(),
        remark=remark_str,
    )
    return ok(data)


@evaluations_bp.get("/history")
@require_auth
def history():
    """Paginated evaluation history for the current user within the tenant."""
    ctx = get_auth_context()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    if page < 1 or page_size < 1 or page_size > 200:
        raise ApiError("Invalid pagination parameters", 400, code="validation_error")

    data = EvaluationService.history(company_id=ctx.company_id, user_id=ctx.user_id, page=page, page_size=page_size)
    return ok(data)
