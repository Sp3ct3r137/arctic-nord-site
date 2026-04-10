# Migrations

Managed by **Alembic** via **Flask-Migrate**.

## First-time setup

```bash
# 1. Make sure DATABASE_URL is set in .env
# 2. Create the database if it doesn't exist yet
#    (psql -U postgres -c "CREATE DATABASE arctic_nord;")

# 3. Run the initial migration
flask db upgrade
```

## Workflow for schema changes

```bash
# After editing models.py:
flask db migrate -m "short description of change"
# Review the generated file in migrations/versions/
flask db upgrade
```

## Rollback

```bash
flask db downgrade          # one step back
flask db downgrade base     # all the way back to empty
```

## Commands

| Command | What it does |
|---------|-------------|
| `flask db init` | Create the migrations/ folder (already done) |
| `flask db migrate -m "msg"` | Auto-generate a migration from model changes |
| `flask db upgrade` | Apply pending migrations to the DB |
| `flask db downgrade` | Revert the last migration |
| `flask db history` | Show migration history |
| `flask db current` | Show current DB revision |
