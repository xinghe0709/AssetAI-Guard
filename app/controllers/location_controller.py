from flask import Blueprint, request

from app.models.user import UserRole
from app.services.location_service import LocationService
from app.utils.auth import get_auth_context, require_roles
from app.utils.errors import ApiError
from app.utils.responses import ok

locations_bp = Blueprint("locations", __name__)


@locations_bp.get("/")
def list_locations():
    """List all shared locations."""
    get_auth_context()
    data = LocationService.list_locations()
    return ok(data)


@locations_bp.post("/")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def create_location():
    """Create a location (admin/manager)."""
    get_auth_context()
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        raise ApiError("name is required", 400, code="validation_error")
    data = LocationService.create_location(name=str(name))
    return ok(data, status_code=201)
