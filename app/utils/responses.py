from typing import Any


def ok(data: Any = None, *, message: str | None = None, status_code: int = 200):
    """Standard success envelope: { success, data?, message? }."""
    payload = {"success": True}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return payload, status_code


def err(*, message: str, status_code: int = 400, code: str | None = None, details: Any = None):
    """Standard error envelope: { success: false, message, code?, details? }."""
    payload: dict[str, Any] = {"success": False, "message": message}
    if code is not None:
        payload["code"] = code
    if details is not None:
        payload["details"] = details
    return payload, status_code
