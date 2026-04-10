#!/usr/bin/env bash
# =============================================================
# setup-https.sh — Arctic Nord: Certbot HTTPS Setup
# =============================================================
# What this script does, in order:
#   1. Asks for your domain name (or reads it from --domain flag)
#   2. Asks for your email address (used by Let's Encrypt for expiry notices)
#   3. Validates both inputs
#   4. Checks that Docker + docker compose are available
#   5. Checks that port 80 is reachable (Certbot needs it for the ACME challenge)
#   6. Runs Certbot in standalone mode to issue the certificate
#   7. Patches nginx/nginx.conf:
#        - Fills YOUR_DOMAIN into the HTTP and HTTPS server blocks
#        - Uncomments the HTTPS server block
#        - Uncomments the HTTP → HTTPS redirect block
#        - Fills cert paths with the real Let's Encrypt paths
#   8. Patches docker-compose.yml:
#        - Uncomments the 443:443 port mapping
#        - Uncomments the /etc/letsencrypt volume mount
#   9. Patches README.md:
#        - Replaces the yourdomain.com placeholder with your real domain
#   10. Backs up every file it modifies (*.bak) before touching it
#   11. Restarts the nginx container to pick up the new config
#   12. Prints a final summary with the live HTTPS URL
#
# Usage:
#   bash scripts/setup-https.sh
#   bash scripts/setup-https.sh --domain example.com --email admin@example.com
#   bash scripts/setup-https.sh --domain example.com --email admin@example.com --dry-run
#
# Flags:
#   --domain   <domain>   Domain to secure (e.g. example.com)
#   --email    <email>    Email for Let's Encrypt renewal notices
#   --dry-run             Run Certbot in test mode (no real cert issued)
#   --help                Show this help text
#
# Requirements:
#   - Certbot installed  (sudo apt install certbot  /  brew install certbot)
#   - Docker + docker compose
#   - Port 80 open and pointed at this machine
#   - Run as root or with sudo privileges
# =============================================================

set -euo pipefail

# ── Colour codes (Nord palette, naturally) ────────────────────
RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
BLU='\033[0;34m'
CYN='\033[0;36m'
ORG='\033[38;5;208m'   # orange — our CTA accent
BLD='\033[1m'
RST='\033[0m'

# ── Resolve script location so paths work from any cwd ───────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

NGINX_CONF="${REPO_ROOT}/nginx/nginx.conf"
COMPOSE_FILE="${REPO_ROOT}/docker-compose.yml"
README_FILE="${REPO_ROOT}/README.md"

# ── Defaults ─────────────────────────────────────────────────
DOMAIN=""
EMAIL=""
DRY_RUN=false
CERTBOT_STAGING=""

# ── Helper functions ──────────────────────────────────────────

log_info()    { echo -e "${CYN}[INFO]${RST}  $*"; }
log_ok()      { echo -e "${GRN}[OK]${RST}    $*"; }
log_warn()    { echo -e "${YLW}[WARN]${RST}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${RST} $*" >&2; }
log_section() { echo -e "\n${ORG}${BLD}── $* ──${RST}"; }

die() {
    log_error "$*"
    exit 1
}

usage() {
    cat <<EOF

${BLD}${ORG}Arctic Nord — HTTPS Setup Script${RST}

Usage:
  bash scripts/setup-https.sh [OPTIONS]

Options:
  --domain  <domain>   Domain name to secure  (e.g. example.com)
  --email   <email>    Email for Let's Encrypt renewal notices
  --dry-run            Certbot staging run — no real cert issued, safe to test
  --help               Show this message

Examples:
  bash scripts/setup-https.sh
  bash scripts/setup-https.sh --domain example.com --email you@example.com
  bash scripts/setup-https.sh --domain example.com --email you@example.com --dry-run

EOF
}

# ── Backup a file before modifying it ────────────────────────
backup_file() {
    local file="$1"
    local backup="${file}.bak"
    cp "$file" "$backup"
    log_info "Backed up ${file} → ${backup}"
}

# ── Validate domain format ────────────────────────────────────
validate_domain() {
    local d="$1"
    # Basic regex: at least one label, a dot, a TLD
    if [[ ! "$d" =~ ^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$ ]]; then
        return 1
    fi
    return 0
}

# ── Validate email format ─────────────────────────────────────
validate_email() {
    local e="$1"
    if [[ ! "$e" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
        return 1
    fi
    return 0
}

# ── Parse CLI arguments ───────────────────────────────────────
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --domain)
                DOMAIN="${2:-}"
                shift 2
                ;;
            --email)
                EMAIL="${2:-}"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                CERTBOT_STAGING="--staging"
                shift
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            *)
                die "Unknown flag: $1  (run with --help)"
                ;;
        esac
    done
}

# ── Prompt for domain if not provided ────────────────────────
prompt_domain() {
    if [[ -n "$DOMAIN" ]]; then
        return
    fi
    echo ""
    echo -e "${BLD}Enter your domain name${RST} (e.g. example.com — no http://, no trailing slash):"
    while true; do
        read -rp "  Domain: " DOMAIN
        DOMAIN="${DOMAIN// /}"   # strip accidental spaces
        if validate_domain "$DOMAIN"; then
            break
        else
            log_warn "That doesn't look like a valid domain. Try again."
        fi
    done
}

# ── Prompt for email if not provided ─────────────────────────
prompt_email() {
    if [[ -n "$EMAIL" ]]; then
        return
    fi
    echo ""
    echo -e "${BLD}Enter your email address${RST} (used by Let's Encrypt for expiry notices):"
    while true; do
        read -rp "  Email: " EMAIL
        EMAIL="${EMAIL// /}"
        if validate_email "$EMAIL"; then
            break
        else
            log_warn "That doesn't look like a valid email. Try again."
        fi
    done
}

# ── Dependency checks ─────────────────────────────────────────
check_deps() {
    log_section "Checking dependencies"

    local missing=()

    command -v certbot      &>/dev/null || missing+=("certbot")
    command -v docker       &>/dev/null || missing+=("docker")

    # docker compose v2 (plugin) or docker-compose v1
    if ! docker compose version &>/dev/null 2>&1 && \
       ! command -v docker-compose &>/dev/null; then
        missing+=("docker-compose")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        echo ""
        echo "Install hints:"
        for t in "${missing[@]}"; do
            case "$t" in
                certbot)         echo "  certbot:          sudo apt install certbot  OR  brew install certbot" ;;
                docker)          echo "  docker:           https://docs.docker.com/get-docker/" ;;
                docker-compose)  echo "  docker compose:   https://docs.docker.com/compose/install/" ;;
            esac
        done
        echo ""
        die "Please install the missing tools and re-run."
    fi

    log_ok "certbot, docker, docker compose — all present"
}

# ── Check required files exist ────────────────────────────────
check_files() {
    log_section "Checking project files"

    for f in "$NGINX_CONF" "$COMPOSE_FILE" "$README_FILE"; do
        [[ -f "$f" ]] || die "Required file not found: $f\nAre you running this from inside the arctic-nord-site repo?"
    done

    log_ok "nginx/nginx.conf, docker-compose.yml, README.md — found"
}

# ── Port 80 open check ────────────────────────────────────────
check_port_80() {
    log_section "Checking port 80"

    # Try to hit ourselves on port 80 — if the healthz endpoint responds
    # we know Nginx is up and the port is reachable from localhost.
    if curl -sf --max-time 5 "http://localhost/healthz" &>/dev/null; then
        log_ok "Port 80 is reachable and Nginx is responding"
        return
    fi

    # Port might be open but Nginx not started yet — that's fine for
    # standalone mode (Certbot will temporarily bind port 80 itself
    # after we stop Nginx).
    log_warn "Could not reach http://localhost/healthz — Nginx may not be running yet."
    log_warn "Certbot standalone mode will bind port 80 itself. Stopping Nginx first..."

    # Stop the nginx container so Certbot can bind port 80
    cd "$REPO_ROOT"
    if docker compose ps nginx 2>/dev/null | grep -q "running"; then
        docker compose stop nginx
        log_ok "Nginx container stopped"
        NGINX_WAS_RUNNING=true
    else
        log_info "Nginx container was not running — no need to stop it"
        NGINX_WAS_RUNNING=false
    fi
}

# ── Run Certbot ───────────────────────────────────────────────
run_certbot() {
    log_section "Running Certbot"

    if [[ "$DRY_RUN" == true ]]; then
        log_warn "DRY RUN mode — using Let's Encrypt staging server (no real cert)"
        log_warn "The cert will NOT be browser-trusted. Remove --dry-run for real certs."
    fi

    echo ""
    echo -e "  Domain : ${BLD}${DOMAIN}${RST}"
    echo -e "  Email  : ${BLD}${EMAIL}${RST}"
    echo -e "  Mode   : ${BLD}$([ "$DRY_RUN" == true ] && echo 'staging (dry-run)' || echo 'production')${RST}"
    echo ""

    # certonly --standalone: Certbot spins up its own temporary HTTP server
    # on port 80 to complete the ACME HTTP-01 challenge.
    certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        --domain "$DOMAIN" \
        ${CERTBOT_STAGING} \
        --keep-until-expiring \
        --expand

    CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
    KEY_PATH="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"

    if [[ "$DRY_RUN" == false ]]; then
        [[ -f "$CERT_PATH" ]] || die "Certificate not found at ${CERT_PATH} — Certbot may have failed."
        log_ok "Certificate issued: ${CERT_PATH}"
    else
        log_ok "Dry-run complete — no real cert written"
        CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
        KEY_PATH="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"
    fi
}

# ── Patch nginx.conf ──────────────────────────────────────────
patch_nginx_conf() {
    log_section "Patching nginx/nginx.conf"

    backup_file "$NGINX_CONF"

    # 1. Replace the catch-all server_name with the real domain
    #    (HTTP block: server_name _;)
    sed -i "s|server_name _;|server_name ${DOMAIN};|g" "$NGINX_CONF"

    # 2. Uncomment the HTTPS server block
    #    The block is wrapped in:  # server {  ... # }
    #    Strategy: remove leading '# ' from every line inside the HTTPS block.
    #    We use a Python one-liner for reliable multi-line sed.
    python3 - <<PYEOF
import re, pathlib

path = pathlib.Path("${NGINX_CONF}")
text = path.read_text()

def uncomment_between_markers(text, begin_marker, end_marker):
    """
    Find everything between begin_marker and end_marker,
    strip the leading '#' (and one optional space) from every line
    inside that region, then drop the marker lines themselves.
    """
    pattern = re.compile(
        r'([ \t]*# ' + re.escape(begin_marker) + r'\n)'
        r'(.*?)'
        r'([ \t]*# ' + re.escape(end_marker) + r'\n)',
        re.DOTALL
    )
    def replacer(m):
        inner = m.group(2)
        # Remove leading '    # ' or '    #' from each line
        unblocked = re.sub(r'(?m)^([ \t]*)# ?', r'\1', inner)
        return unblocked   # drop marker lines
    return pattern.sub(replacer, text, count=1)

# Uncomment the HTTPS server block
text = uncomment_between_markers(text, 'SETUP-HTTPS-BEGIN', 'SETUP-HTTPS-END')

# Uncomment the HTTP→HTTPS redirect block
text = uncomment_between_markers(text, 'SETUP-REDIRECT-BEGIN', 'SETUP-REDIRECT-END')

# Replace all yourdomain.com occurrences with the real domain
text = text.replace('yourdomain.com', '${DOMAIN}')

path.write_text(text)
print("nginx.conf patched OK")
PYEOF

    log_ok "nginx/nginx.conf updated — domain: ${DOMAIN}, HTTPS block uncommented"
}

# ── Patch docker-compose.yml ──────────────────────────────────
patch_compose() {
    log_section "Patching docker-compose.yml"

    backup_file "$COMPOSE_FILE"

    python3 - <<PYEOF
import re, pathlib

path = pathlib.Path("${COMPOSE_FILE}")
text = path.read_text()

# Uncomment  # - "443:443"
text = re.sub(r'#\s*- "443:443"', '      - "443:443"', text)

# Uncomment  # - /etc/letsencrypt:/etc/letsencrypt:ro
text = re.sub(
    r'#\s*- /etc/letsencrypt:/etc/letsencrypt:ro',
    '      - /etc/letsencrypt:/etc/letsencrypt:ro',
    text
)

# Uncomment  # - /var/www/certbot:/var/www/certbot:ro
text = re.sub(
    r'#\s*- /var/www/certbot:/var/www/certbot:ro',
    '      - /var/www/certbot:/var/www/certbot:ro',
    text
)

path.write_text(text)
print("docker-compose.yml patched OK")
PYEOF

    log_ok "docker-compose.yml updated — port 443 and letsencrypt volume uncommented"
}

# ── Patch README.md ───────────────────────────────────────────
patch_readme() {
    log_section "Patching README.md"

    backup_file "$README_FILE"

    sed -i "s|yourdomain\.com|${DOMAIN}|g" "$README_FILE"

    log_ok "README.md updated — yourdomain.com → ${DOMAIN}"
}

# ── Restart Nginx ─────────────────────────────────────────────
restart_nginx() {
    log_section "Restarting Nginx"

    cd "$REPO_ROOT"

    # Validate the new nginx config before restarting
    log_info "Validating nginx config..."
    docker run --rm \
        -v "${REPO_ROOT}/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" \
        nginx:1.27-alpine nginx -t 2>&1 \
    && log_ok "nginx -t passed" \
    || die "nginx config validation failed — check nginx/nginx.conf"

    # Rebuild and restart
    docker compose up -d --build nginx

    log_ok "Nginx restarted with HTTPS config"
}

# ── Auto-renew cron ───────────────────────────────────────────
setup_cron() {
    log_section "Setting up auto-renew cron"

    # Certbot renew checks every 12 hours; only renews if < 30 days left.
    # After renewal, reload nginx inside the container.
    local cron_line="0 0,12 * * * certbot renew --quiet && docker compose -f ${REPO_ROOT}/docker-compose.yml exec nginx nginx -s reload"

    # Add to crontab only if not already present
    if crontab -l 2>/dev/null | grep -qF "certbot renew"; then
        log_info "certbot renew cron already exists — skipping"
    else
        ( crontab -l 2>/dev/null; echo "$cron_line" ) | crontab -
        log_ok "Cron added: certbot renew runs at midnight and noon daily"
    fi
}

# ── Summary ───────────────────────────────────────────────────
print_summary() {
    echo ""
    echo -e "${ORG}${BLD}══════════════════════════════════════════${RST}"
    echo -e "${ORG}${BLD}  Arctic Nord — HTTPS Setup Complete       ${RST}"
    echo -e "${ORG}${BLD}══════════════════════════════════════════${RST}"
    echo ""
    echo -e "  ${GRN}✓${RST} Certificate issued for ${BLD}${DOMAIN}${RST}"
    echo -e "  ${GRN}✓${RST} nginx.conf patched and HTTPS block active"
    echo -e "  ${GRN}✓${RST} docker-compose.yml: port 443 + letsencrypt volume enabled"
    echo -e "  ${GRN}✓${RST} README.md updated with your domain"
    echo -e "  ${GRN}✓${RST} Auto-renew cron installed (runs twice daily)"
    echo ""
    echo -e "  ${BLD}Your site:${RST}"
    echo -e "    ${CYN}http://${DOMAIN}${RST}   → redirects to HTTPS"
    echo -e "    ${CYN}https://${DOMAIN}${RST}  → Arctic Nord site"
    echo ""
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "  ${YLW}⚠  This was a DRY RUN — run without --dry-run to issue a real cert${RST}"
        echo ""
    fi
    echo -e "  Backups of modified files:"
    echo -e "    nginx/nginx.conf.bak"
    echo -e "    docker-compose.yml.bak"
    echo -e "    README.md.bak"
    echo ""
    echo -e "  To roll back: ${BLD}cp nginx/nginx.conf.bak nginx/nginx.conf${RST} etc."
    echo ""
}

# ── Main ──────────────────────────────────────────────────────
main() {
    echo ""
    echo -e "${ORG}${BLD}❄  Arctic Nord — HTTPS / Certbot Setup${RST}"
    echo -e "${BLU}    Powered by Let's Encrypt + Nginx + Docker${RST}"
    echo ""

    parse_args "$@"
    prompt_domain
    prompt_email

    # Validate inputs if they came from flags (prompts validate inline)
    validate_domain "$DOMAIN" || die "Invalid domain: ${DOMAIN}"
    validate_email  "$EMAIL"  || die "Invalid email: ${EMAIL}"

    check_deps
    check_files
    check_port_80
    run_certbot
    patch_nginx_conf
    patch_compose
    patch_readme
    restart_nginx
    setup_cron
    print_summary
}

main "$@"
