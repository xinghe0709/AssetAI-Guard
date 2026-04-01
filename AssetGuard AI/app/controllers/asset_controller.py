from flask import Blueprint, current_app, request

from app.models.user import UserRole
from app.services.asset_service import AssetService
from app.utils.auth import get_auth_context, require_roles
from app.utils.errors import ApiError
from app.utils.responses import ok

assets_bp = Blueprint("assets", __name__)


@assets_bp.get("/")
def list_assets():
    """
    List assets for a location.

    Query: locationId (required), page, pageSize, optional q (name search).
    """
    _ = get_auth_context()
    location_id = request.args.get("locationId", type=int)
    if location_id is None:
        raise ApiError("locationId is required", 400, code="validation_error")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    q = request.args.get("q")
    if page < 1 or page_size < 1 or page_size > 200:
        raise ApiError("Invalid pagination parameters", 400, code="validation_error")

    data = AssetService.list_assets(
        location_id=location_id,
        page=page,
        page_size=page_size,
        q=q,
    )
    return ok(data)


@assets_bp.get("/all")
def list_all_assets():
    """List all assets."""
    _ = get_auth_context()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    q = request.args.get("q")
    if page < 1 or page_size < 1 or page_size > 200:
        raise ApiError("Invalid pagination parameters", 400, code="validation_error")
    data = AssetService.list_all_assets(
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

    JSON: locationName, name, loadCapacities: [{ name, metric, maxLoad, details? }]
    """
    _ = get_auth_context()
    body = request.get_json(silent=True) or {}
    location_name = body.get("locationName")
    name = body.get("name")
    load_capacities = body.get("loadCapacities")
    if location_name is None or not str(location_name).strip():
        raise ApiError("locationName is required", 400, code="validation_error")
    if not isinstance(load_capacities, list):
        raise ApiError("loadCapacities must be an array", 400, code="validation_error")

    data = AssetService.create_asset(
        location_name=str(location_name),
        name=str(name or ""),
        load_capacities=load_capacities,
    )
    return ok(data, status_code=201)


@assets_bp.post("/import-json-uploads")
@require_roles(UserRole.SYSTEM_ADMIN.value)
def import_json_uploads():
    """
    Import all asset-payload JSON files from the AI uploads directory into the current DB.
    Optional JSON body: { directoryPath }
    """
    _ = get_auth_context()
    body = request.get_json(silent=True) or {}
    directory_path = body.get("directoryPath") or current_app.config.get("AI_JSON_UPLOADS_DIR")
    if not directory_path:
        raise ApiError("directoryPath is required", 400, code="validation_error")

    data = AssetService.import_assets_from_json_directory(
        directory_path=str(directory_path),
    )
    status_code = 201 if data.get("createdCount", 0) > 0 else 200
    return ok(data, status_code=status_code)


@assets_bp.get("/<int:asset_id>/load-capacities")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def list_load_capacities(asset_id: int):
    _ = get_auth_context()
    data = AssetService.list_load_capacities(asset_id=asset_id)
    return ok(data)


@assets_bp.post("/<int:asset_id>/load-capacities")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def create_load_capacity(asset_id: int):
    _ = get_auth_context()
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    metric = body.get("metric")
    max_load = body.get("maxLoad")
    details = body.get("details")
    if name is None or metric is None or max_load is None:
        raise ApiError("name, metric, and maxLoad are required", 400, code="validation_error")
    data = AssetService.create_load_capacity(
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
    _ = get_auth_context()
    body = request.get_json(silent=True) or {}
    if not any(k in body for k in ("name", "metric", "maxLoad", "details")):
        raise ApiError(
            "At least one of name, metric, maxLoad, details must be provided",
            400,
            code="validation_error",
        )
    data = AssetService.update_load_capacity(
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
    _ = get_auth_context()
    AssetService.delete_load_capacity(
        asset_id=asset_id,
        capacity_id=capacity_id,
    )
    return ok({"deleted": True})
