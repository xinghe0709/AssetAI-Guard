from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Callable

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.models import User
from app.models.user import UserRole
from app.utils.errors import ApiError


@dataclass(frozen=True)
class AuthContext:
    """Current user context parsed from the Bearer token (includes tenant id)."""

    user_id: int
    company_id: int
    role: str
    email: str


def _serializer() -> URLSafeTimedSerializer:
    """Signed token serializer (itsdangerous); secret from SECRET_KEY."""
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="assetguard-token")


def issue_token(*, user: User) -> str:
    """Issue a token whose payload includes user_id, company_id, role, and email."""
    payload = {
        "user_id": user.id,
        "company_id": user.company_id,
        "role": user.role.value if isinstance(user.role, UserRole) else str(user.role),
        "email": user.email,
    }
    return _serializer().dumps(payload)


def verify_token(token: str) -> AuthContext:
    """
    Verify signature and expiry, then build AuthContext.

    - 401 token_expired / token_invalid on failure
    """
    try:
        payload = _serializer().loads(
            token,
            max_age=current_app.config.get("TOKEN_EXPIRES_SECONDS", 86400),
        )
    except SignatureExpired as e:
        raise ApiError("Token has expired; please sign in again", 401, code="token_expired") from e
    except BadSignature as e:
        raise ApiError("Invalid token", 401, code="token_invalid") from e

    for k in ("user_id", "company_id", "role", "email"):
        if k not in payload:
            raise ApiError("Invalid token payload", 401, code="token_invalid")

    return AuthContext(
        user_id=int(payload["user_id"]),
        company_id=int(payload["company_id"]),
        role=str(payload["role"]),
        email=str(payload["email"]),
    )


def get_auth_context() -> AuthContext:
    """Read Authorization: Bearer <token> and return AuthContext."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise ApiError("Missing Bearer token", 401, code="missing_token")
    token = header.removeprefix("Bearer ").strip()
    if not token:
        raise ApiError("Missing Bearer token", 401, code="missing_token")
    return verify_token(token)


def require_auth(fn: Callable):
    """Route decorator: require a valid Bearer token."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        _ = get_auth_context()
        return fn(*args, **kwargs)

    return wrapper


def require_roles(*roles: str):
    """Route decorator: require one of the given roles (RBAC)."""

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ctx = get_auth_context()
            if ctx.role not in roles:
                raise ApiError("Forbidden", 403, code="forbidden", details={"required_roles": roles})
            return fn(*args, **kwargs)

        return wrapper

    return decorator
