"""
app.py — Arctic Nord Flask Application
=======================================
Entry point for the Arctic Nord themed website.
Serves all HTML pages via Flask routes and exposes
a lightweight JSON API endpoint for demo purposes.

Author : Zero Ch1ll
Stack  : Python 3 / Flask
Theme  : Arctic Nord (#2E3440 base) + Orange accent (#D08770)
"""

from flask import Flask, render_template, jsonify
from datetime import datetime

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Context processor — injects the current year into every template
# so the footer copyright stays fresh automatically.
# ---------------------------------------------------------------------------

@app.context_processor
def inject_globals():
    """Make shared template variables available site-wide."""
    return {
        "current_year": datetime.now().year,
        "site_name": "Arctic Nord",
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
