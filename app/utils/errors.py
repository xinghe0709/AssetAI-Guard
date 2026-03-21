from flask import Flask
from werkzeug.exceptions import HTTPException

from app.utils.responses import err


class ApiError(Exception):
    """
    Expected business failure (validation, auth, not found, etc.).

    Fields:
    - message: human-readable text
    - status_code: HTTP status
    - code: machine-readable code for clients
    - details: optional structured payload
    """

    def __init__(self, message: str, status_code: int = 400, code: str | None = None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


def register_error_handlers(app: Flask) -> None:
    """Register global handlers for ApiError, HTTPException, and unexpected errors."""

    @app.errorhandler(ApiError)
    def handle_api_error(e: ApiError):
        return err(message=e.message, status_code=e.status_code, code=e.code, details=e.details)

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        return err(message=e.description, status_code=e.code or 500, code="http_error")

    @app.errorhandler(Exception)
    def handle_unexpected_error(e: Exception):
        return err(message="Internal Server Error", status_code=500, code="internal_error")
