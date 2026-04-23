from flask import Blueprint, request

from app.models.user import UserRole
from app.services.alert_service import AlertService
from app.utils.auth import require_roles
from app.utils.errors import ApiError
from app.utils.responses import ok

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("/email-logs")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def email_logs():
    limit = int(request.args.get("limit", 100))
    if limit < 1 or limit > 500:
        raise ApiError("Invalid limit parameter", 400, code="validation_error")
    return ok({"items": AlertService.get_logs(limit=limit)})


@alerts_bp.get("/email-preferences")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def get_email_preferences():
    return ok(AlertService.get_preferences())


@alerts_bp.put("/email-preferences")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def put_email_preferences():
    payload = request.get_json(silent=True) or {}
    return ok(AlertService.update_preferences(payload))


@alerts_bp.get("/email-template")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def get_email_template():
    return ok(AlertService.get_template())


@alerts_bp.put("/email-template")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def put_email_template():
    payload = request.get_json(silent=True) or {}
    return ok(AlertService.update_template(payload))


@alerts_bp.post("/test-email")
@require_roles(UserRole.SYSTEM_ADMIN.value, UserRole.ASSET_MANAGER.value)
def post_test_email():
    return ok(AlertService.send_test_email())
