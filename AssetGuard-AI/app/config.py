import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration loaded from environment variables / .env file."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///assetguard.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TOKEN_EXPIRES_SECONDS = int(os.getenv("TOKEN_EXPIRES_SECONDS", "86400"))
    AI_IMPORT_BASE_URL = os.getenv("AI_IMPORT_BASE_URL", "http://127.0.0.1:5001")
    AI_IMPORT_TIMEOUT_SECONDS = int(os.getenv("AI_IMPORT_TIMEOUT_SECONDS", "60"))
    AI_JSON_UPLOADS_DIR = os.getenv(
        "AI_JSON_UPLOADS_DIR",
        str(Path(__file__).resolve().parents[2] / "gjp-assetguard-extraction-tool" / "uploads"),
    )

    # SMTP / Mailtrap sandbox settings
    SMTP_SUPPRESS_SEND = os.getenv("SMTP_SUPPRESS_SEND", "false").lower() == "true"
    SMTP_HOST = os.getenv("SMTP_HOST", "sandbox.smtp.mailtrap.io")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@assetguard.ai")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
