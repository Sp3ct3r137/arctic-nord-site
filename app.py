"""
app.py — Arctic Nord Flask Application
=======================================
Entry point for the Arctic Nord themed website.
Now uses an application factory (create_app) so Flask-Migrate,
Flask-Login, and other extensions can be initialised properly.

Author : Zero Ch1ll
Stack  : Python 3 / Flask + SQLAlchemy + PostgreSQL
Theme  : Arctic Nord (#2E3440 base) + Orange accent (#D08770)

Environment variables (set in .env):
    SECRET_KEY          — Flask session signing key
    DATABASE_URL        — PostgreSQL connection string
    FERNET_KEY          — Encryption key for OAuth tokens
"""

import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from datetime import datetime
from dotenv import load_dotenv

# Load .env file (does nothing if already set in environment)
load_dotenv()


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    """
    Create and configure the Flask application.
    Using a factory allows extensions to be initialised without circular
    imports and makes the app testable (just call create_app() in tests).
    """
    app = Flask(__name__)

    # ── Core config ───────────────────────────────────────────
    # SECRET_KEY signs session cookies — must be random and secret in prod.
    # Generate: python -c "import secrets; print(secrets.token_hex(32))"
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-production")

    # ── Database ──────────────────────────────────────────────
    # DATABASE_URL from .env, e.g.:
    #   postgresql://user:password@localhost:5432/arctic_nord
    # SQLite fallback for local dev without PostgreSQL:
    #   sqlite:///arctic_nord.db
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///arctic_nord.db"   # fallback: SQLite for local dev
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,   # reconnect if connection dropped
    }

    # ── Session cookie security ───────────────────────────────
    app.config["SESSION_COOKIE_HTTPONLY"] = True    # JS cannot read cookie
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # CSRF protection
    # Set to True in production (requires HTTPS):
    app.config["SESSION_COOKIE_SECURE"]   = os.environ.get("FLASK_ENV") == "production"
    app.config["REMEMBER_COOKIE_HTTPONLY"]= True
    app.config["REMEMBER_COOKIE_SECURE"]  = os.environ.get("FLASK_ENV") == "production"

    # ── Initialise extensions ─────────────────────────────────
    from extensions import db, login_manager, bcrypt, limiter
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    # ── Register blueprints ───────────────────────────────────
    from routes.auth     import auth_bp
    from routes.settings import settings_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_bp)

    # ── Register all page routes ──────────────────────────────
    _register_routes(app)

    return app


# ---------------------------------------------------------------------------
# Backward-compat: top-level `app` for Gunicorn / python app.py
# ---------------------------------------------------------------------------
app = create_app()


# ---------------------------------------------------------------------------
# Route registration helper (called inside create_app)
# ---------------------------------------------------------------------------

def _register_routes(app: Flask):
    """Attach all view functions and context processors to the app instance."""

    @app.context_processor
    def inject_globals():
        """Make shared template variables available site-wide."""
        from flask_login import current_user
        return {
            "current_year": datetime.now().year,
            "site_name": "Arctic Nord",
            "current_user": current_user,
        }


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Home page — hero section, feature cards, about blurb."""
    features = [
        {
            "icon": "❄️",
            "title": "Polar Night",
            "desc": "Deep, dark backgrounds drawn from Nord's Polar Night palette "
                    "(nord0–nord3) keep the UI calm and focused.",
        },
        {
            "icon": "🌨️",
            "title": "Snow Storm",
            "desc": "Crisp text and surface colours from the Snow Storm group "
                    "(nord4–nord6) ensure comfortable readability at any hour.",
        },
        {
            "icon": "🧊",
            "title": "Frost",
            "desc": "Primary interactive elements use the four Frost shades "
                    "(nord7–nord10) — cyan-blues that pop without shouting.",
        },
        {
            "icon": "🔥",
            "title": "Orange Accent",
            "desc": "A warm nord12 (#D08770) orange layered on top gives the "
                    "palette energy and draws the eye to calls-to-action.",
        },
    ]
    return render_template("index.html", features=features)


@app.route("/about")
def about():
    """About page — explains the project, the palette, and the stack."""
    palette = [
        # Polar Night
        {"group": "Polar Night", "name": "nord0",  "hex": "#2E3440", "role": "Page background"},
        {"group": "Polar Night", "name": "nord1",  "hex": "#3B4252", "role": "Elevated surfaces / cards"},
        {"group": "Polar Night", "name": "nord2",  "hex": "#434C5E", "role": "Hover states / selection"},
        {"group": "Polar Night", "name": "nord3",  "hex": "#4C566A", "role": "Subtle borders / muted text"},
        # Snow Storm
        {"group": "Snow Storm", "name": "nord4",  "hex": "#D8DEE9", "role": "Secondary text"},
        {"group": "Snow Storm", "name": "nord5",  "hex": "#E5E9F0", "role": "Primary text"},
        {"group": "Snow Storm", "name": "nord6",  "hex": "#ECEFF4", "role": "Headings / emphasis"},
        # Frost
        {"group": "Frost", "name": "nord7",  "hex": "#8FBCBB", "role": "Calm accent / icons"},
        {"group": "Frost", "name": "nord8",  "hex": "#88C0D0", "role": "Primary interactive accent"},
        {"group": "Frost", "name": "nord9",  "hex": "#81A1C1", "role": "Links / secondary accent"},
        {"group": "Frost", "name": "nord10", "hex": "#5E81AC", "role": "Deep accent / badges"},
        # Aurora / Orange
        {"group": "Aurora + Custom Orange", "name": "nord12 / orange", "hex": "#D08770", "role": "⚡ CTA accent (orange)"},
    ]
    return render_template("about.html", palette=palette)


@app.route("/docs")
def documentation():
    """Documentation page — architecture, file tree, and usage notes."""
    return render_template("docs.html")


@app.route("/subscribe", methods=["GET", "POST"])
def subscribe():
    """
    Subscription page.

    GET  — renders the page with tier cards and the signup form.
    POST — handles the form submission. Currently echoes data back as a
           thank-you confirmation. Wire this to your payment provider
           (Stripe, PayPal, etc.) or mailing list (Mailchimp, etc.) here.

    EDIT THIS SECTION to customise tiers:
      - name        : displayed tier name
      - price       : price string shown on the card  (e.g. "$9 / mo")
      - description : one-line pitch
      - features    : list of bullet points shown on the card
      - highlight   : True = orange CTA border (marks recommended tier)
      - badge       : short label shown in the corner (e.g. "Popular")
      - value       : internal identifier passed with the form submission
    """
    # ----------------------------------------------------------------
    # TIERS — edit freely. Add, remove, or reorder dicts in this list.
    # ----------------------------------------------------------------
    tiers = [
        {
            "name":        "Frost",
            "price":       "Free",
            "period":      "",
            "description": "Get started with the basics. No credit card needed.",
            "features": [
                "Access to core features",
                "Community support via Discord",
                "1 project",
                "Nord theme included",
            ],
            "highlight":   False,
            "badge":       "",
            "value":       "frost",
        },
        {
            "name":        "Polar",
            "price":       "$9",
            "period":      "/ month",
            "description": "Everything in Frost, plus priority features and more projects.",
            "features": [
                "Everything in Frost",
                "Up to 10 projects",
                "Priority email support",
                "Custom domain",
                "Analytics dashboard",
            ],
            "highlight":   True,
            "badge":       "Popular",
            "value":       "polar",
        },
        {
            "name":        "Aurora",
            "price":       "$29",
            "period":      "/ month",
            "description": "Full power. Unlimited everything, dedicated support.",
            "features": [
                "Everything in Polar",
                "Unlimited projects",
                "Dedicated Slack channel",
                "SLA: 99.9% uptime",
                "Early access to new features",
                "Custom integrations",
            ],
            "highlight":   False,
            "badge":       "Enterprise",
            "value":       "aurora",
        },
    ]

    # ----------------------------------------------------------------
    # Form submission handler
    # EDIT: replace the flash/redirect with your real payment / email
    # list logic. The submitted values are available as:
    #   name  = request.form.get("name")
    #   email = request.form.get("email")
    #   tier  = request.form.get("tier")   (matches tier["value"])
    # ----------------------------------------------------------------
    if request.method == "POST":
        name  = request.form.get("name",  "").strip()
        email = request.form.get("email", "").strip()
        tier  = request.form.get("tier",  "frost")

        # Basic server-side validation
        if not name or not email:
            flash("Please fill in both your name and email.", "error")
            return render_template("subscribe.html", tiers=tiers)

        # --- HOOK YOUR LOGIC HERE ---
        # e.g. stripe.checkout.Session.create(...)
        # e.g. mailchimp.lists.members.create(...)
        # ----------------------------

        # For now: redirect to confirmation with query params
        return redirect(url_for(
            "subscribe_confirm",
            name=name,
            tier=tier,
        ))

    return render_template("subscribe.html", tiers=tiers)


@app.route("/subscribe/confirm")
def subscribe_confirm():
    """
    Thank-you confirmation page shown after a successful subscription form.
    Receives `name` and `tier` as query parameters from the subscribe route.
    """
    name = request.args.get("name", "there")
    tier = request.args.get("tier", "frost").capitalize()
    return render_template("subscribe_confirm.html", name=name, tier=tier)


# ---------------------------------------------------------------------------
# Demo API — returns colour data as JSON so the site shows a live endpoint
# ---------------------------------------------------------------------------

@app.route("/api/palette")
def api_palette():
    """
    GET /api/palette
    Returns the full Nord + orange palette as a JSON array.
    Each entry contains: name, hex, group, and role.
    """
    data = [
        {"name": "nord0",  "hex": "#2E3440", "group": "Polar Night",  "role": "Background"},
        {"name": "nord1",  "hex": "#3B4252", "group": "Polar Night",  "role": "Elevated surface"},
        {"name": "nord2",  "hex": "#434C5E", "group": "Polar Night",  "role": "Hover / selection"},
        {"name": "nord3",  "hex": "#4C566A", "group": "Polar Night",  "role": "Border / muted"},
        {"name": "nord4",  "hex": "#D8DEE9", "group": "Snow Storm",   "role": "Secondary text"},
        {"name": "nord5",  "hex": "#E5E9F0", "group": "Snow Storm",   "role": "Primary text"},
        {"name": "nord6",  "hex": "#ECEFF4", "group": "Snow Storm",   "role": "Headings"},
        {"name": "nord7",  "hex": "#8FBCBB", "group": "Frost",        "role": "Calm accent"},
        {"name": "nord8",  "hex": "#88C0D0", "group": "Frost",        "role": "Primary accent"},
        {"name": "nord9",  "hex": "#81A1C1", "group": "Frost",        "role": "Links"},
        {"name": "nord10", "hex": "#5E81AC", "group": "Frost",        "role": "Deep accent"},
        {"name": "orange", "hex": "#D08770", "group": "Aurora/Custom","role": "CTA accent"},
    ]
    return jsonify({"palette": data, "count": len(data)})


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Debug mode is fine for local dev; set debug=False in production.
    app.run(debug=True, port=5000)
