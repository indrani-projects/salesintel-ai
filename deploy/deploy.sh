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

echo "==> render + install Caddyfile (host: $SITE_HOST)"
sed "s/__SITE_HOST__/$SITE_HOST/g" "$HERE/Caddyfile" > /etc/caddy/Caddyfile

echo "==> fix ownership + (re)start services"
chown -R "$APP_USER:$APP_USER" "$APP_DIR/backend"
systemctl restart salesintel
systemctl reload caddy 2>/dev/null || systemctl restart caddy

echo "==> done. App: https://$SITE_HOST   (health: https://$SITE_HOST/api/health)"
