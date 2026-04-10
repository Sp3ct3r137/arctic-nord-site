"""
models.py — SQLAlchemy ORM Models
==================================
Tables:
    users           — account identity + bcrypt password hash
    oauth_tokens    — OAuth provider tokens (encrypted at rest)
    subscriptions   — subscription tier per user
    user_settings   — per-user preferences (theme, notifications, etc.)
    sessions        — server-side session store (hashed tokens)

All timestamps use timezone-aware UTC datetimes.
Relationships are defined with lazy="select" (load on access).

Encryption:
    OAuth tokens are encrypted with Fernet (symmetric AES-128-CBC + HMAC).
    The encryption key is read from the FERNET_KEY environment variable.
    Generate a key with:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import os
import hashlib
import secrets
from datetime import datetime, timezone

from flask_login import UserMixin
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Index

from extensions import db


# ── Encryption helpers (OAuth tokens) ─────────────────────────

def _get_fernet() -> Fernet:
    """
    Load the Fernet encryption key from the environment.
    Raises RuntimeError if the key is missing or invalid — fail loud in dev,
    don't silently fall back to unencrypted storage.
    """
    key = os.environ.get("FERNET_KEY")
    if not key:
        raise RuntimeError(
            "FERNET_KEY environment variable is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt_token(value: str) -> str:
    """Encrypt a plaintext token string. Returns a URL-safe base64 string."""
    if not value:
        return ""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_token(value: str) -> str:
    """Decrypt an encrypted token. Returns empty string on failure."""
    if not value:
        return ""
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except (InvalidToken, Exception):
        return ""


# ── users ──────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    """
    Core account record.

    Flask-Login requires UserMixin which provides default implementations
    of is_authenticated, is_active, is_anonymous, and get_id().

    Password is NEVER stored — only bcrypt hash.
    """
    __tablename__ = "users"

    id              = db.Column(db.Integer,     primary_key=True)
    email           = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username        = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    password_hash   = db.Column(db.String(255), nullable=False)

    # Account state
    is_active       = db.Column(db.Boolean, default=True,  nullable=False)
    is_verified     = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps (all UTC)
    created_at      = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login      = db.Column(db.DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────
    oauth_tokens    = db.relationship("OAuthToken",    back_populates="user", cascade="all, delete-orphan", lazy="select")
    subscription    = db.relationship("Subscription",  back_populates="user", uselist=False, cascade="all, delete-orphan")
    settings        = db.relationship("UserSettings",  back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions        = db.relationship("UserSession",   back_populates="user", cascade="all, delete-orphan", lazy="select")

    # ── Flask-Login: active check ─────────────────────────────
    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    # SQLAlchemy needs the column to have a different internal name when we
    # also define a property. Use a synonym or rename the column:
    _is_active = db.Column("is_active", db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<User id={self.id} email={self.email!r}>"


# ── oauth_tokens ───────────────────────────────────────────────

class OAuthToken(db.Model):
    """
    Stores OAuth 2.0 access and refresh tokens for a user + provider pair.
    Tokens are encrypted at rest using Fernet (AES-128-CBC + HMAC-SHA256).

    Supported providers (examples): "google", "github", "discord"
    Add more by registering them in routes/auth.py with Authlib.
    """
    __tablename__ = "oauth_tokens"

    id                    = db.Column(db.Integer,     primary_key=True)
    user_id               = db.Column(db.Integer,     db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider              = db.Column(db.String(50),  nullable=False)           # e.g. "google"
    provider_user_id      = db.Column(db.String(255), nullable=True)            # provider's own user ID

    # Encrypted token fields — use encrypt_token() / decrypt_token() helpers
    _access_token         = db.Column("access_token",  db.Text, nullable=False)
    _refresh_token        = db.Column("refresh_token", db.Text, nullable=True)

    expires_at            = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at            = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at            = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                      onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="oauth_tokens")

    # Unique constraint: one token record per user per provider
    __table_args__ = (
        db.UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),
    )

    # ── Encrypted property accessors ──────────────────────────
    @property
    def access_token(self) -> str:
        return decrypt_token(self._access_token)

    @access_token.setter
    def access_token(self, value: str):
        self._access_token = encrypt_token(value)

    @property
    def refresh_token(self) -> str:
        return decrypt_token(self._refresh_token or "")

    @refresh_token.setter
    def refresh_token(self, value: str):
        self._refresh_token = encrypt_token(value) if value else None

    def __repr__(self):
        return f"<OAuthToken user_id={self.user_id} provider={self.provider!r}>"


# ── subscriptions ──────────────────────────────────────────────

class Subscription(db.Model):
    """
    One subscription record per user (one-to-one with User).
    Tier values mirror the tier['value'] keys defined in app.py:
        "frost"  — free tier
        "polar"  — $9/mo
        "aurora" — $29/mo

    Status values:
        "active"      — currently paying / on free tier
        "cancelled"   — cancelled but access until period end
        "past_due"    — payment failed, grace period
        "trialing"    — on trial (if you add trials later)

    EDIT: add a stripe_subscription_id column when you wire Stripe.
    """
    __tablename__ = "subscriptions"

    TIERS    = ("frost", "polar", "aurora")
    STATUSES = ("active", "cancelled", "past_due", "trialing")

    id          = db.Column(db.Integer,    primary_key=True)
    user_id     = db.Column(db.Integer,    db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    tier        = db.Column(db.String(20), nullable=False, default="frost")
    status      = db.Column(db.String(20), nullable=False, default="active")

    # Stripe / payment provider IDs — empty until wired
    stripe_customer_id       = db.Column(db.String(255), nullable=True)
    stripe_subscription_id   = db.Column(db.String(255), nullable=True)

    created_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    renewed_at  = db.Column(db.DateTime(timezone=True), nullable=True)
    cancelled_at= db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription user_id={self.user_id} tier={self.tier!r} status={self.status!r}>"


# ── user_settings ──────────────────────────────────────────────

class UserSettings(db.Model):
    """
    Per-user preferences. One row per user (one-to-one with User).

    The `extra` JSONB column acts as an escape hatch — store arbitrary
    key/value pairs here without a schema migration. Use it for low-traffic
    settings that don't need to be queried or indexed.

    EDIT: add new preference columns here as you build out the product.
    """
    __tablename__ = "user_settings"

    id                   = db.Column(db.Integer,     primary_key=True)
    user_id              = db.Column(db.Integer,     db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Theme preference — synced with the JS theme toggle
    theme                = db.Column(db.String(10),  nullable=False, default="dark")  # "dark" | "light"

    # Notification preferences
    email_notifications  = db.Column(db.Boolean,    nullable=False, default=True)
    marketing_emails     = db.Column(db.Boolean,    nullable=False, default=False)

    # Display preferences
    timezone             = db.Column(db.String(50),  nullable=False, default="UTC")
    language             = db.Column(db.String(10),  nullable=False, default="en")

    # Escape hatch for arbitrary settings without migrations
    # Stored as JSONB on PostgreSQL, JSON on SQLite
    extra                = db.Column(db.JSON,        nullable=False, default=dict)

    updated_at           = db.Column(db.DateTime(timezone=True),
                                     default=lambda: datetime.now(timezone.utc),
                                     onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="settings")

    def __repr__(self):
        return f"<UserSettings user_id={self.user_id} theme={self.theme!r}>"


# ── sessions ───────────────────────────────────────────────────

class UserSession(db.Model):
    """
    Server-side session store for tracking active logins.

    Why server-side sessions?
      - Allows instant revocation (logout all devices, ban user)
      - Token is hashed before storage — DB leak doesn't expose live tokens
      - Stores IP + user-agent for audit / suspicious login detection

    The raw session token is generated by auth.py and stored in the
    client cookie. On each request, Flask-Login hashes it and looks up
    this table to validate.

    EDIT: call UserSession.cleanup_expired() in a scheduled task to
    prune old rows.
    """
    __tablename__ = "user_sessions"

    id           = db.Column(db.Integer,     primary_key=True)
    user_id      = db.Column(db.Integer,     db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # SHA-256 hash of the raw session token stored in the cookie
    token_hash   = db.Column(db.String(64),  nullable=False, unique=True, index=True)

    # Audit fields
    ip_address   = db.Column(db.String(45),  nullable=True)   # supports IPv6
    user_agent   = db.Column(db.String(512), nullable=True)

    created_at   = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at   = db.Column(db.DateTime(timezone=True), nullable=False)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="sessions")

    # Index for fast expiry cleanup queries
    __table_args__ = (
        Index("ix_user_sessions_expires_at", "expires_at"),
    )

    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure random session token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """SHA-256 hash of a token. Store this, never the raw token."""
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def cleanup_expired(cls):
        """Delete all expired session rows. Call from a scheduled task."""
        cls.query.filter(cls.expires_at < datetime.now(timezone.utc)).delete()
        db.session.commit()

    def __repr__(self):
        return f"<UserSession user_id={self.user_id} ip={self.ip_address!r}>"


# ── Flask-Login user loader ────────────────────────────────────

from extensions import login_manager

@login_manager.user_loader
def load_user(user_id: str):
    """
    Called by Flask-Login on every request to reload the user from the session.
    Returns None if the user doesn't exist or is inactive.
    """
    return db.session.get(User, int(user_id))
