# =============================================================
# Dockerfile — Arctic Nord Flask App (Gunicorn)
# =============================================================
# This image runs only the Flask/Gunicorn WSGI server.
# Nginx runs as a SEPARATE container (see docker-compose.yml).
#
# Build:  docker build -t arctic-nord-app .
# Run:    docker run -p 8000:8000 arctic-nord-app
#         (or use docker-compose — recommended)
# =============================================================

# ── Stage 1: dependency builder ───────────────────────────────
# Use a full image to compile any C-extension wheels, then
# copy only the installed packages into the slim final image.
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools (needed for some pip packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies into a prefix directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────
FROM python:3.12-slim AS runtime

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose Gunicorn port — Nginx will connect here
EXPOSE 8000

# Gunicorn settings:
#   --workers      = (2 × CPU cores) + 1 is a common starting point
#   --worker-class = sync (default) is fine for this Flask app
#   --bind         = 0.0.0.0:8000 so Nginx can reach it from its container
#   --forwarded-allow-ips = trust X-Forwarded-For from Nginx
CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--forwarded-allow-ips", "*"]
