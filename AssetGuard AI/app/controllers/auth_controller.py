from flask import Blueprint, request

from app.models.user import UserRole
from app.services.auth_service import AuthService
from app.utils.auth import get_auth_context, require_roles
from app.utils.errors import ApiError
from app.utils.responses import ok

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    """Sign in with email/password; returns Bearer token and minimal user info."""
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    if not email or not password:
        raise ApiError("email and password are required", 400, code="validation_error")

    data = AuthService.login(email=email, password=password)
    return ok(data)


@auth_bp.post("/change-password")
def change_password():
    """
    Change the authenticated user's password.

    JSON body: currentPassword, newPassword.
    Any authenticated user may call this endpoint.
    """
    ctx = get_auth_context()
    body = request.get_json(silent=True) or {}

    current_password = body.get("currentPassword") or ""
    new_password = body.get("newPassword") or ""

    if not current_password or not new_password:
        raise ApiError("currentPassword and newPassword are required", 400, code="validation_error")

    AuthService.change_password(
        user_id=ctx.user_id,
        current_password=current_password,
        new_password=new_password,
    )
    return ok({"message": "Password changed successfully"})


@auth_bp.post("/users")
@require_roles(UserRole.SYSTEM_ADMIN.value)
def create_user():
    """
    Create a user (System_Admin only).

    JSON body: email, password, role (System_Admin | Asset_Manager | Contractors).
    """
    _ = get_auth_context()
    body = request.get_json(silent=True) or {}

    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    role_str = (body.get("role") or "").strip()

    if not email or not password or not role_str:
        raise ApiError("email, password, and role are required", 400, code="validation_error")

    try:
        role = UserRole(role_str)
    except ValueError as e:
        raise ApiError(
            "Invalid role; allowed: System_Admin, Asset_Manager, Contractors",
            400,
            code="validation_error",
        ) from e

    user = AuthService.create_user(
        email=email,
        password=password,
        role=role,
    )

    return ok(
        {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
        },
        status_code=201,
    )
