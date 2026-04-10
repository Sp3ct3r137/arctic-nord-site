"""
routes/settings.py — User Settings Blueprint
=============================================
Routes:
    GET  /settings          — settings page (login required)
    POST /settings          — save preferences
    POST /settings/theme    — JSON endpoint: sync JS theme toggle → DB
    POST /settings/password — change password
    POST /settings/delete   — delete account (requires password confirmation)

All routes require login via @login_required.
"""

from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, jsonify, current_app
)
from flask_login import login_required, current_user, logout_user

from extensions import db, bcrypt

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


# ── Settings page ─────────────────────────────────────────────

@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """
    GET  — render the settings form pre-filled with the user's current prefs
    POST — validate and save updated preferences
    """
    settings = current_user.settings

    if request.method == "POST":
        action = request.form.get("action", "save_prefs")

        # ── Save general preferences ──────────────────────────
        if action == "save_prefs":
            theme               = request.form.get("theme", "dark")
            email_notifications = bool(request.form.get("email_notifications"))
            marketing_emails    = bool(request.form.get("marketing_emails"))
            timezone_pref       = request.form.get("timezone", "UTC")[:50]
            language            = request.form.get("language", "en")[:10]

            if theme not in ("dark", "light"):
                theme = "dark"

            settings.theme               = theme
            settings.email_notifications = email_notifications
            settings.marketing_emails    = marketing_emails
            settings.timezone            = timezone_pref
            settings.language            = language
            settings.updated_at          = datetime.now(timezone.utc)

            db.session.commit()
            flash("Preferences saved.", "success")
            return redirect(url_for("settings.index"))

        # ── Save email / username ─────────────────────────────
        if action == "save_account":
            new_username = request.form.get("username", "").strip().lower()
            new_email    = request.form.get("email",    "").strip().lower()
            errors = []

            if not new_username or len(new_username) < 3:
                errors.append("Username must be at least 3 characters.")
            if not new_email or "@" not in new_email:
                errors.append("A valid email is required.")

            # Check uniqueness (excluding current user)
            from models import User
            if not errors:
                taken_u = User.query.filter(
                    User.username == new_username,
                    User.id != current_user.id
                ).first()
                taken_e = User.query.filter(
                    User.email == new_email,
                    User.id != current_user.id
                ).first()
                if taken_u:
                    errors.append("That username is already taken.")
                if taken_e:
                    errors.append("That email is already registered.")

            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                current_user.username = new_username
                current_user.email    = new_email
                db.session.commit()
                flash("Account details updated.", "success")

            return redirect(url_for("settings.index"))

    return render_template("settings.html", settings=settings, user=current_user)


# ── Theme sync endpoint ────────────────────────────────────────

@settings_bp.route("/theme", methods=["POST"])
@login_required
def sync_theme():
    """
    POST /settings/theme
    Body: { "theme": "dark" | "light" }

    Called by theme.js whenever the user toggles the theme while logged in,
    so their preference is persisted to the DB and restored on next login
    even from a different browser.

    Returns: { "ok": true, "theme": "<applied>" }
    """
    data  = request.get_json(silent=True) or {}
    theme = data.get("theme", "dark")

    if theme not in ("dark", "light"):
        return jsonify({"ok": False, "error": "Invalid theme"}), 400

    if current_user.settings:
        current_user.settings.theme      = theme
        current_user.settings.updated_at = datetime.now(timezone.utc)
        db.session.commit()

    return jsonify({"ok": True, "theme": theme})


# ── Change password ────────────────────────────────────────────

@settings_bp.route("/password", methods=["POST"])
@login_required
def change_password():
    """
    POST /settings/password
    Form fields: current_password, new_password, confirm_password
    """
    current_pw  = request.form.get("current_password", "")
    new_pw      = request.form.get("new_password",      "")
    confirm_pw  = request.form.get("confirm_password",  "")

    errors = []

    if not bcrypt.check_password_hash(current_user.password_hash, current_pw):
        errors.append("Current password is incorrect.")
    if len(new_pw) < 8:
        errors.append("New password must be at least 8 characters.")
    if new_pw != confirm_pw:
        errors.append("New passwords do not match.")

    if errors:
        for e in errors:
            flash(e, "error")
    else:
        current_user.password_hash = bcrypt.generate_password_hash(new_pw).decode("utf-8")
        db.session.commit()
        flash("Password updated successfully.", "success")

    return redirect(url_for("settings.index"))


# ── Delete account ─────────────────────────────────────────────

@settings_bp.route("/delete", methods=["POST"])
@login_required
def delete_account():
    """
    POST /settings/delete
    Requires the user to confirm their password before deletion.
    Cascades delete to all related rows via FK ON DELETE CASCADE.
    """
    confirm_pw = request.form.get("confirm_password", "")

    if not bcrypt.check_password_hash(current_user.password_hash, confirm_pw):
        flash("Incorrect password — account not deleted.", "error")
        return redirect(url_for("settings.index"))

    user = current_user
    logout_user()

    db.session.delete(user)
    db.session.commit()

    flash("Your account has been permanently deleted.", "success")
    return redirect(url_for("index"))
