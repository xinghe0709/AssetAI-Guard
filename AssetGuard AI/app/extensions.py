from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Shared extensions; initialized with init_app in the app factory to avoid circular imports.
db = SQLAlchemy()
migrate = Migrate()
