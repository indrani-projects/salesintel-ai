#!/usr/bin/env bash
# Deploy / refresh SalesIntel AI on the VM. Run AFTER bootstrap.sh and after the
# code payload has been synced to /opt/salesintel (must contain backend/, docs/,
# frontend/dist/, and backend/.cache/ for the prepared research docs). Idempotent.
#
#   SITE_HOST=salesintel-you.duckdns.org sudo -E bash /opt/salesintel/deploy/deploy.sh
#
# -E preserves SITE_HOST through sudo. The env file (/etc/salesintel/env) must
# already exist with real secrets (see env.production.example) — this script never
# writes secrets.
set -euo pipefail

APP_USER=salesintel
APP_DIR=/opt/salesintel
WWW_DIR=/var/www/salesintel
VENV="$APP_DIR/backend/.venv"
SITE_HOST="${SITE_HOST:?set SITE_HOST=your.duckdns.org}"
HERE="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -f /etc/salesintel/env ]]; then
	echo "!! /etc/salesintel/env is missing — create it from deploy/env.production.example first." >&2
	exit 1
fi

echo "==> secure the secrets file (chmod 600, owned by $APP_USER)"
chown "$APP_USER:$APP_USER" /etc/salesintel/env
chmod 600 /etc/salesintel/env

echo "==> python venv + dependencies"
sudo -u "$APP_USER" python3 -m venv "$VENV" 2>/dev/null || true
sudo -u "$APP_USER" "$VENV/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$VENV/bin/pip" install -r "$APP_DIR/backend/requirements.txt"

echo "==> publish built frontend -> $WWW_DIR"
rsync -a --delete "$APP_DIR/frontend/dist/" "$WWW_DIR/"

echo "==> install systemd unit"
cp "$HERE/salesintel.service" /etc/systemd/system/salesintel.service
systemctl daemon-reload
systemctl enable salesintel

echo "==> render Caddyfile (host: $SITE_HOST) + inject access gate"
# Read the gate credentials LITERALLY (grep/cut, never `source`) so the bcrypt hash's
# `$` characters aren't shell-expanded.
DEMO_AUTH_USER="$(grep -E '^DEMO_AUTH_USER=' /etc/salesintel/env | head -1 | cut -d= -f2- || true)"
DEMO_AUTH_HASH="$(grep -E '^DEMO_AUTH_HASH=' /etc/salesintel/env | head -1 | cut -d= -f2- || true)"

AUTH_BLOCK=""
if [[ -n "$DEMO_AUTH_HASH" && "$DEMO_AUTH_HASH" != __* ]]; then
	# health + OAuth callback stay open; everything else needs the shared password.
	printf -v AUTH_BLOCK '\t@gated not path /api/health /api/auth/google/*\n\tbasic_auth @gated {\n\t\t%s %s\n\t}' \
		"${DEMO_AUTH_USER:-demo}" "$DEMO_AUTH_HASH"
	echo "   access gate: ON (user ${DEMO_AUTH_USER:-demo})"
else
	echo "   !! DEMO_AUTH_HASH not set — deploying WITHOUT the access gate" >&2
fi

RENDERED="$(mktemp)"
export AUTH_BLOCK
sed "s/__SITE_HOST__/$SITE_HOST/g" "$HERE/Caddyfile" \
	| awk '{ if ($0 ~ /__BASICAUTH_BLOCK__/) { printf "%s\n", ENVIRON["AUTH_BLOCK"] } else { print } }' \
	> "$RENDERED"

# Validate BEFORE touching the live config — a broken Caddyfile must never take the
# site down. Only install + reload if it validates clean.
if ! caddy validate --adapter caddyfile --config "$RENDERED" 2>/tmp/caddy-validate.log; then
	echo "!! rendered Caddyfile failed validation — keeping the CURRENT config:" >&2
	cat /tmp/caddy-validate.log >&2
	rm -f "$RENDERED"
	exit 1
fi
cp "$RENDERED" /etc/caddy/Caddyfile
rm -f "$RENDERED"

echo "==> fix ownership + (re)start services"
chown -R "$APP_USER:$APP_USER" "$APP_DIR/backend"
systemctl restart salesintel
systemctl reload caddy 2>/dev/null || systemctl restart caddy

echo "==> done. App: https://$SITE_HOST   (health: https://$SITE_HOST/api/health)"
