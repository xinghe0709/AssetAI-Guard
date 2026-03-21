import os


class Config:
    """
    Central configuration (environment variables).

    - DATABASE_URL / SQLALCHEMY_DATABASE_URI: DB connection (default SQLite file)
    - SECRET_KEY: token signing secret (override in production)
    - TOKEN_EXPIRES_SECONDS: Bearer token lifetime
    """

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///assetguard.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TOKEN_EXPIRES_SECONDS = int(os.getenv("TOKEN_EXPIRES_SECONDS", "86400"))
