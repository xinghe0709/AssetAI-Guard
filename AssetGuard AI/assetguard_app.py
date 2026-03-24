"""
WSGI entrypoint exposing `app` for Flask CLI and production servers.

Common commands:
  python -m flask --app assetguard_app.py run
  python -m flask --app assetguard_app.py db upgrade
  python -m flask --app assetguard_app.py seed
"""

from app import create_app

app = create_app()
