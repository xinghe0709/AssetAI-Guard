from flask import Blueprint, request

from app.models.user import UserRole
from app.services.asset_service import AssetService
from app.utils.auth import get_auth_context, require_roles
from app.utils.errors import ApiError
from app.utils.responses import ok

assets_bp = Blueprint("assets", __name__)


@assets_bp.get("/")
def list_assets():
    """List assets for the current company (requires login). Query: page, pageSize, optional q."""
    ctx = get_auth_context()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    q = request.args.get("q")
    if page < 1 or page_size < 1 or page_size > 200:
        raise ApiError("Invalid pagination parameters", 400, code="validation_error")

    data = AssetService.list_assets(company_id=ctx.company_id, page=page, page_size=page_size, q=q)
    return ok(data)


@assets_bp.post("/")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def create_asset():
    """
    Create an asset (System_Admin or Asset_Manager).

    JSON: assetName, maxLoadCapacity (required); equipmentType, unit, sourceFile (optional).
    unit must be English: kg, ton (or t), lb (or lbs). Defaults to kg if omitted.
    """
    ctx = get_auth_context()
    body = request.get_json(silent=True) or {}

    asset_name = (body.get("assetName") or "").strip()
    max_load_capacity = body.get("maxLoadCapacity")
    equipment_type = (body.get("equipmentType") or None)
    unit = (body.get("unit") or None)
    source_file = (body.get("sourceFile") or None)

    if not asset_name:
        raise ApiError("assetName is required", 400, code="validation_error")
    if max_load_capacity is None:
        raise ApiError("maxLoadCapacity is required", 400, code="validation_error")

    try:
        max_load_capacity_f = float(max_load_capacity)
    except (TypeError, ValueError) as e:
        raise ApiError("maxLoadCapacity must be a number", 400, code="validation_error") from e

    data = AssetService.create_asset(
        company_id=ctx.company_id,
        asset_name=asset_name,
        equipment_type=equipment_type,
        max_load_capacity=max_load_capacity_f,
        unit=unit,
        source_file=source_file,
    )
    return ok(data, status_code=201)


@assets_bp.post("/bulk-import")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def bulk_import():
    """Placeholder: bulk import from an external AI pipeline (not implemented)."""
    raise ApiError(
        "bulk-import is not implemented (requires external AI integration)",
        501,
        code="not_implemented",
    )
