from flask import Blueprint, request

from app.models.user import UserRole
from app.services.asset_service import AssetService
from app.utils.auth import get_auth_context, require_roles
from app.utils.errors import ApiError
from app.utils.responses import ok

assets_bp = Blueprint("assets", __name__)


@assets_bp.get("/")
def list_assets():
    """
    List assets for a location (tenant-scoped).

    Query: locationId (required), page, pageSize, optional q (name search).
    """
    ctx = get_auth_context()
    location_id = request.args.get("locationId", type=int)
    if location_id is None:
        raise ApiError("locationId is required", 400, code="validation_error")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    q = request.args.get("q")
    if page < 1 or page_size < 1 or page_size > 200:
        raise ApiError("Invalid pagination parameters", 400, code="validation_error")

    data = AssetService.list_assets(
        company_id=ctx.company_id,
        location_id=location_id,
        page=page,
        page_size=page_size,
        q=q,
    )
    return ok(data)


@assets_bp.get("/all")
def list_company_assets():
    """List all assets visible to current company."""
    ctx = get_auth_context()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    q = request.args.get("q")
    if page < 1 or page_size < 1 or page_size > 200:
        raise ApiError("Invalid pagination parameters", 400, code="validation_error")
    data = AssetService.list_company_assets(
        company_id=ctx.company_id,
        page=page,
        page_size=page_size,
        q=q,
    )
    return ok(data)


@assets_bp.post("/")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def create_asset():
    """
    Create an asset with load capacities (PDF structure).

    JSON: locationId, name, loadCapacities: [{ name, metric, maxLoad, details? }]
    """
    ctx = get_auth_context()
    body = request.get_json(silent=True) or {}
    location_id = body.get("locationId")
    name = body.get("name")
    load_capacities = body.get("loadCapacities")
    if location_id is None:
        raise ApiError("locationId is required", 400, code="validation_error")
    try:
        lid = int(location_id)
    except (TypeError, ValueError) as e:
        raise ApiError("locationId must be an integer", 400, code="validation_error") from e
    if not isinstance(load_capacities, list):
        raise ApiError("loadCapacities must be an array", 400, code="validation_error")

    data = AssetService.create_asset(
        company_id=ctx.company_id,
        location_id=lid,
        name=str(name or ""),
        load_capacities=load_capacities,
    )
    return ok(data, status_code=201)


@assets_bp.post("/bulk-import")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def bulk_import():
    """Placeholder for future AI / structured bulk ingest."""
    raise ApiError(
        "bulk-import is not implemented (requires external AI integration)",
        501,
        code="not_implemented",
    )


@assets_bp.get("/<int:asset_id>/load-capacities")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def list_load_capacities(asset_id: int):
    ctx = get_auth_context()
    data = AssetService.list_load_capacities(company_id=ctx.company_id, asset_id=asset_id)
    return ok(data)


@assets_bp.post("/<int:asset_id>/load-capacities")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def create_load_capacity(asset_id: int):
    ctx = get_auth_context()
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    metric = body.get("metric")
    max_load = body.get("maxLoad")
    details = body.get("details")
    if name is None or metric is None or max_load is None:
        raise ApiError("name, metric, and maxLoad are required", 400, code="validation_error")
    data = AssetService.create_load_capacity(
        company_id=ctx.company_id,
        asset_id=asset_id,
        name=str(name),
        metric_raw=str(metric),
        max_load=max_load,
        details=(str(details) if details is not None else None),
    )
    return ok(data, status_code=201)


@assets_bp.put("/<int:asset_id>/load-capacities/<int:capacity_id>")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def update_load_capacity(asset_id: int, capacity_id: int):
    ctx = get_auth_context()
    body = request.get_json(silent=True) or {}
    if not any(k in body for k in ("name", "metric", "maxLoad", "details")):
        raise ApiError(
            "At least one of name, metric, maxLoad, details must be provided",
            400,
            code="validation_error",
        )
    data = AssetService.update_load_capacity(
        company_id=ctx.company_id,
        asset_id=asset_id,
        capacity_id=capacity_id,
        name=(str(body["name"]) if "name" in body and body["name"] is not None else None),
        metric_raw=(
            str(body["metric"]) if "metric" in body and body["metric"] is not None else None
        ),
        max_load=(body["maxLoad"] if "maxLoad" in body else None),
        details=(str(body["details"]) if "details" in body and body["details"] is not None else None),
    )
    return ok(data)


@assets_bp.delete("/<int:asset_id>/load-capacities/<int:capacity_id>")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def delete_load_capacity(asset_id: int, capacity_id: int):
    ctx = get_auth_context()
    AssetService.delete_load_capacity(
        company_id=ctx.company_id,
        asset_id=asset_id,
        capacity_id=capacity_id,
    )
    return ok({"deleted": True})
