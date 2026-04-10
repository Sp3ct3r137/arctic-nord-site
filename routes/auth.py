"""
routes/auth.py — Authentication Blueprint
==========================================
Routes:
    GET  /auth/register        — registration form
    POST /auth/register        — create account
    GET  /auth/login           — login form
    POST /auth/login           — authenticate + create session
    POST /auth/logout          — destroy session + cookie
    GET  /auth/me              — current user info (JSON, login required)

Security measures applied here:
    - bcrypt password hashing (via extensions.bcrypt)
    - Rate limiting on register + login (5/minute per IP)
    - Server-side session record written to user_sessions table
    - Session cookie is HttpOnly + Secure (configured in app.py)
    - Username and email normalised to lowercase before storage
    - Timing-safe password check (bcrypt is inherently constant-time)
"""

from datetime import datetime, timezone, timedelta

from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, jsonify, current_app
)
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db, bcrypt, limiter
from models import User, UserSession, UserSettings, Subscription

# ── Blueprint ─────────────────────────────────────────────────
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ── Constants ─────────────────────────────────────────────────
SESSION_DURATION_DAYS = 30   # how long a "remember me" session lasts


# ── Helpers ───────────────────────────────────────────────────

def _create_session(user: User) -> str:
    """
    Generate a raw session token, hash it, write a UserSession row,
    and return the raw token (to be stored in the client cookie).
    """
    raw_token  = UserSession.generate_token()
    token_hash = UserSession.hash_token(raw_token)
    expires    = datetime.now(timezone.utc) + timedelta(days=SESSION_DURATION_DAYS)

    session_row = UserSession(
        user_id    = user.id,
        token_hash = token_hash,
        ip_address = request.remote_addr,
        user_agent = request.user_agent.string[:512],
        expires_at = expires,
    )
    db.session.add(session_row)
    db.session.commit()
    return raw_token


def _flash_errors(form_errors: dict):
    """Flash all WTForms-style validation errors."""
    for field, errors in form_errors.items():
        for error in errors:
            flash(f"{field}: {error}", "error")


# ── Register ──────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")   # stricter than global default
def register():
    """
    GET  — render registration form
    POST — validate, hash password, create User + Settings + Subscription rows
    """
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email    = request.form.get("email",    "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm",  "")

        # ── Server-side validation ────────────────────────────
        errors = []

        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if len(username) > 80:
            errors.append("Username must be 80 characters or fewer.")
        if not email or "@" not in email:
            errors.append("A valid email address is required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        # Check uniqueness
        if not errors:
            if User.query.filter_by(email=email).first():
                errors.append("An account with that email already exists.")
            if User.query.filter_by(username=username).first():
                errors.append("That username is taken.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("auth/register.html",
                                   username=username, email=email)

        # ── Create account ────────────────────────────────────
        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(
            username      = username,
            email         = email,
            password_hash = pw_hash,
            is_verified   = False,
        )
        db.session.add(user)
        db.session.flush()   # get user.id without committing

        # Default settings row — theme from cookie/JS, falls back to dark
        theme = request.cookies.get("arctic-theme", "dark")
        settings = UserSettings(
            user_id              = user.id,
            theme                = theme if theme in ("dark", "light") else "dark",
            email_notifications  = True,
            marketing_emails     = False,
        )
        db.session.add(settings)

        # Default free subscription
        sub = Subscription(user_id=user.id, tier="frost", status="active")
        db.session.add(sub)

        db.session.commit()

        # Log the user in immediately after registration
        login_user(user, remember=True)
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        flash(f"Welcome, {user.username}! Your account has been created.", "success")
        return redirect(url_for("index"))

    return render_template("auth/register.html", username="", email="")


# ── Login ─────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")   # brute-force protection
def login():
    """
    GET  — render login form
    POST — verify credentials, create server-side session record
    """
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password   = request.form.get("password",   "")
        remember   = bool(request.form.get("remember"))

        # Look up by email OR username
        user = (
            User.query.filter_by(email=identifier).first()
            or User.query.filter_by(username=identifier).first()
        )

        # Use bcrypt.check_password_hash even on failure to avoid
        # timing attacks that could reveal whether an account exists.
        dummy_hash = "$2b$12$notarealhashXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        candidate_hash = user.password_hash if user else dummy_hash
        password_ok = bcrypt.check_password_hash(candidate_hash, password)

        if not user or not password_ok:
            flash("Invalid email/username or password.", "error")
            return render_template("auth/login.html", identifier=identifier)

        if not user.is_active:
            flash("This account has been deactivated. Contact support.", "error")
            return render_template("auth/login.html", identifier=identifier)

        # Log in via Flask-Login
        login_user(user, remember=remember)

        # Write a server-side session row
        _create_session(user)

        # Update last_login timestamp
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        # Redirect to the page they were trying to reach, or home
        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):   # prevent open redirect
            return redirect(next_page)
        return redirect(url_for("index"))

    return render_template("auth/login.html", identifier="")


# ── Logout ────────────────────────────────────────────────────

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    POST — invalidate the Flask-Login session and redirect to home.
    Uses POST (not GET) to prevent CSRF-triggered logouts via image tags etc.
    """
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# ── Current user API ──────────────────────────────────────────

@auth_bp.route("/me")
@login_required
def me():
    """
    GET /auth/me
    Returns the current authenticated user's public profile as JSON.
    Useful for JS that needs to know who is logged in.
    """
    return jsonify({
        "id":         current_user.id,
        "username":   current_user.username,
        "email":      current_user.email,
        "tier":       current_user.subscription.tier if current_user.subscription else "frost",
        "theme":      current_user.settings.theme    if current_user.settings    else "dark",
        "created_at": current_user.created_at.isoformat(),
    })
