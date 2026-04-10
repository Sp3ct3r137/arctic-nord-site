"""
extensions.py — Shared Flask extension instances
=================================================
All extensions are instantiated here WITHOUT being bound to an app.
They are registered in app.py via the init_app() pattern, which lets
the extensions be imported by models.py and routes without causing
circular imports.

Importing order in app.py:
    from extensions import db, login_manager, bcrypt, limiter
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ── Database (SQLAlchemy ORM → PostgreSQL via psycopg2) ───────
# All models import `db` from here and call db.Model as their base.
db = SQLAlchemy()

# ── Login manager (Flask-Login) ────────────────────────────────
# Handles user session loading, @login_required, and redirects.
login_manager = LoginManager()
login_manager.login_view     = "auth.login"        # redirect here if not logged in
login_manager.login_message  = "Please log in to access that page."
login_manager.login_message_category = "error"

# ── Password hashing (bcrypt) ──────────────────────────────────
# Never store plain passwords. Use:
#   bcrypt.generate_password_hash(password).decode("utf-8")
#   bcrypt.check_password_hash(stored_hash, candidate)
bcrypt = Bcrypt()

# ── Rate limiter (Flask-Limiter) ───────────────────────────────
# Default limits applied globally. Override per-route with @limiter.limit().
# Auth routes use stricter limits defined in routes/auth.py.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://",   # swap for Redis URI in production:
                               # storage_uri=os.environ.get("REDIS_URL")
)
