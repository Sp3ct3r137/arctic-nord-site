"""
migrations/env.py — Alembic migration environment
==================================================
This file is run by Alembic when generating or applying migrations.
It imports the Flask app and SQLAlchemy metadata so Alembic can
diff the current schema against the models and generate migrations
automatically with:

    flask db migrate -m "description"
    flask db upgrade

Setup (first time):
    pip install -r requirements.txt
    flask db init        # creates the migrations/ folder (already done)
    flask db migrate -m "initial schema"
    flask db upgrade     # applies to the database
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Import the Flask app and db so Alembic sees the models ────
# We use an app factory pattern via create_app() defined in app.py.
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from extensions import db

flask_app = create_app()

# Alembic Config object from alembic.ini
config = context.config

# Override sqlalchemy.url from the Flask app config so we only
# maintain the DATABASE_URL in one place (.env).
config.set_main_option(
    "sqlalchemy.url",
    flask_app.config.get("SQLALCHEMY_DATABASE_URI", "")
)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy MetaData — Alembic uses this to detect schema changes
target_metadata = db.metadata


# ── Offline mode (generate SQL without a live DB connection) ──
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,        # detect column type changes
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (apply migrations with a live DB connection) ──
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
