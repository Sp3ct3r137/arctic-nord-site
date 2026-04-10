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

Flask's built-in server is **development only**.

### Option A — Docker Compose + Nginx (recommended)

This is the full production stack: Nginx handles static files and TLS,
Gunicorn runs the Flask app behind it.

```bash
# Build and start both containers
docker compose up -d --build

# Tail logs
docker compose logs -f

# Stop
docker compose down
```

**What runs:**

| Container | Image | Port | Role |
|-----------|-------|------|------|
| `arctic-nord-nginx` | `nginx:1.27-alpine` | `80` (public) | Reverse proxy, static files, gzip |
| `arctic-nord-app`  | Built from `Dockerfile` | `8000` (internal only) | Gunicorn / Flask WSGI |

Nginx serves `/static/` directly from a shared Docker volume — CSS and JS
never hit Python. Everything else is proxied to Gunicorn.

### Option B — Gunicorn only (bare metal / PaaS)

```bash
pip install -r requirements.txt
gunicorn app:app --bind 0.0.0.0:8000 --workers 4
```

One-click PaaS hosts: **Railway**, **Render**, **Fly.io** — push the repo and
set the start command to `gunicorn app:app --bind 0.0.0.0:8000`.

### Nginx config highlights (`nginx/nginx.conf`)

- **Reverse proxy** — all non-static requests forwarded to `app:8000`
- **Static file serving** — `/static/` aliased to the shared volume; 30-day cache headers
- **Gzip** — enabled for CSS, JS, JSON, SVG
- **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`
- **Health check** — `GET /healthz` returns `200 ok` for load balancers
- **HTTPS** — full TLS server block included, commented out; fill in cert paths and uncomment

### Enabling HTTPS (Let's Encrypt)

Run the setup script — it handles everything automatically:

```bash
# Interactive (prompts for domain + email)
sudo bash scripts/setup-https.sh

# Non-interactive (pass flags directly)
sudo bash scripts/setup-https.sh --domain yourdomain.com --email you@yourdomain.com

# Dry run — test the full flow without issuing a real cert
sudo bash scripts/setup-https.sh --domain yourdomain.com --email you@yourdomain.com --dry-run
```

**What the script does in order:**

1. Prompts for your domain and email (or reads from `--domain` / `--email` flags)
2. Validates both inputs before touching anything
3. Checks that `certbot`, `docker`, and `docker compose` are installed
4. Stops the Nginx container so port 80 is free for the ACME challenge
5. Runs `certbot certonly --standalone` to issue the Let's Encrypt certificate
6. Patches `nginx/nginx.conf` — fills in your domain, uncomments the full HTTPS server block and the HTTP→HTTPS redirect block
7. Patches `docker-compose.yml` — uncomments port `443:443` and the `/etc/letsencrypt` volume mount
8. Patches this `README.md` — replaces `yourdomain.com` with your real domain
9. Backs up every modified file (`*.bak`) before touching it
10. Validates the new Nginx config with `nginx -t` before restarting
11. Restarts the Nginx container
12. Installs a cron job to auto-renew the cert twice daily

**Requirements:**
- `certbot` installed (`sudo apt install certbot`)
- Docker + docker compose running
- Port 80 pointed at this machine
- Run with `sudo` (Certbot needs root to write to `/etc/letsencrypt`)

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
