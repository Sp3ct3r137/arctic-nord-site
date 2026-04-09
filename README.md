# ❄️ Arctic Nord — Flask Website

> A minimal Python / Flask website dressed in the full
> [Nord colour palette](https://www.nordtheme.com) — Polar Night backgrounds,
> Snow Storm typography, Frost interactive elements, and a single warm
> **orange** accent (`#D08770 / nord12`) to guide the eye.

---

## Preview

| Page | What's on it |
|------|-------------|
| `/`        | Hero + animated snowflake canvas + API demo terminal |
| `/about`   | Full colour palette swatches + tech stack table      |
| `/docs`    | Quick-start, file tree, route reference, deployment  |
| `/api/palette` | JSON — all 12 palette entries                    |

---

## Quick Start

```bash
# 1 — clone
git clone https://github.com/Sp3ct3r137/arctic-nord-site.git
cd arctic-nord-site

# 2 — virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3 — install dependencies
pip install -r requirements.txt

# 4 — run
python app.py
```

Open **http://localhost:5000** in your browser.

---

## File Structure

```
arctic-nord-site/
├── app.py                  # Flask app — routes, context processor, JSON API
├── requirements.txt        # Flask >= 3.0
├── README.md               # this file
│
├── templates/
│   ├── base.html           # shared layout (nav, footer, fonts, favicon)
│   ├── index.html          # home — hero, feature cards, API demo
│   ├── about.html          # palette swatches, tech stack
│   └── docs.html           # full documentation page
│
├── static/
│   ├── css/
│   │   └── style.css       # all styles — Nord CSS tokens + components
│   └── js/
│       └── main.js         # canvas snow, fetch demo, scroll FX
│
└── docs/
    └── COLOURS.md          # standalone colour reference with role table
```

---

## How It Works

### 1. Flask Routes (`app.py`)

Each page is a plain Python function decorated with `@app.route`:

```python
@app.route("/")
def index():
    features = [...]   # passed into Jinja2 template
    return render_template("index.html", features=features)
```

A `@app.context_processor` injects `current_year` and `site_name` into
**every** template automatically — no need to pass them per-route.

### 2. Template Inheritance (`templates/`)

All pages extend `base.html` using Jinja2 blocks:

```html
{% extends "base.html" %}

{% block title %}My Page — Arctic Nord{% endblock %}

{% block content %}
  <!-- page-specific HTML here -->
{% endblock %}
```

`base.html` handles the `<head>`, nav, footer, font loading, and favicon.

### 3. Colour System (`static/css/style.css`)

All 16 Nord colours are defined as CSS custom properties in `:root`,
plus three orange-accent steps:

```css
:root {
  /* Polar Night */
  --nord0: #2E3440;   /* page background */
  --nord1: #3B4252;   /* elevated surfaces */

  /* Orange accent (from Aurora / nord12) */
  --orange:       #D08770;
  --orange-light: #E09880;   /* hover */
  --orange-dim:   #A06050;   /* active */

  /* Semantic aliases — use these in component CSS */
  --color-bg:    var(--nord0);
  --color-cta:   var(--orange);
  --color-accent: var(--nord8);
}
```

Component styles **only** reference semantic aliases. Change a raw Nord
value in one place and the whole site updates.

### 4. JavaScript (`static/js/main.js`)

Three features — no external libraries:

| Feature | Technique |
|---------|-----------|
| Snowflake canvas | `requestAnimationFrame` Canvas 2D — particles + rotating geometric snowflake |
| API demo | `fetch("/api/palette")` → renders JSON into a styled terminal UI |
| Card reveal | `IntersectionObserver` — fades cards in as they scroll into view |

### 5. JSON API (`/api/palette`)

`Flask.jsonify()` returns the colour data:

```json
{
  "count": 12,
  "palette": [
    { "name": "nord0", "hex": "#2E3440", "group": "Polar Night", "role": "Background" },
    ...
  ]
}
```

Extend it with query-string filtering or connect a database for dynamic themes.

---

## Colour Palette

See [`docs/COLOURS.md`](docs/COLOURS.md) for the full table.

Quick reference:

| Group | Hex range | Used for |
|-------|-----------|----------|
| Polar Night (`nord0–3`) | `#2E3440` → `#4C566A` | Backgrounds, surfaces, borders |
| Snow Storm (`nord4–6`) | `#D8DEE9` → `#ECEFF4` | Text, headings |
| Frost (`nord7–10`) | `#8FBCBB` → `#5E81AC` | Interactive, accent, links |
| Orange (nord12) | `#D08770` | ⚡ CTAs, highlights |

### Why orange?

`nord12` (`#D08770`) is part of Nord's Aurora group — a warm, muted orange
that sits naturally against the cold blue-grey Polar Night backgrounds.
It creates strong visual contrast for calls-to-action without breaking the
Arctic aesthetic. One warm colour against 15 cold ones is enough.

---

## Production Deployment

Flask's built-in server is **development only**. Run Gunicorn in production:

```bash
pip install gunicorn
gunicorn app:app --bind 0.0.0.0:8000 --workers 4
```

### Minimal Dockerfile (Google Cloud Run / any container host)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "2"]
```

One-click hosts: **Railway**, **Render**, **Fly.io** — push the repo and set
the start command to `gunicorn app:app`.

---

## Extending

### Add a page

1. Add a route in `app.py`
2. Create `templates/your-page.html` extending `base.html`
3. Add a nav link in `base.html` → `.nav__links`

### Add a new component style

Open `static/css/style.css` and reference only semantic token variables
(`--color-bg`, `--color-cta`, etc.) — never hard-code hex values.

### Add an API endpoint

```python
@app.route("/api/my-data")
def my_data():
    return jsonify({"key": "value"})
```

---

## Dependencies

| Package | Version | Why |
|---------|---------|-----|
| Flask   | ≥ 3.0   | Web framework — routing, Jinja2, `jsonify` |

Zero frontend dependencies — plain HTML, CSS, and vanilla JavaScript.

---

## Credits

- Colour palette: [Arctic Ice Studio — Nord](https://www.nordtheme.com)
- Fonts: [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) + [Inter](https://fonts.google.com/specimen/Inter) via Google Fonts
- Built by Zero Ch1ll / Sp3ct3r137
