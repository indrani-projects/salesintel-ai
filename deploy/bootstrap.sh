#!/usr/bin/env bash
# One-time VM setup for SalesIntel AI on Ubuntu (22.04/24.04). Idempotent — safe to
# re-run. Installs system deps, the Caddy web server, the service user, the data
# directories, and enables automatic security updates. Run with sudo on the VM:
#   sudo bash /opt/salesintel/deploy/bootstrap.sh
set -euo pipefail

APP_USER=salesintel
APP_DIR=/opt/salesintel
DB_DIR=/var/lib/salesintel
WWW_DIR=/var/www/salesintel
ENV_DIR=/etc/salesintel

export DEBIAN_FRONTEND=noninteractive

echo "==> apt: base packages"
apt-get update -y
apt-get install -y \
	python3-venv python3-pip rsync curl gpg \
	debian-keyring debian-archive-keyring apt-transport-https \
	unattended-upgrades

echo "==> service user + directories"
id -u "$APP_USER" &>/dev/null || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
mkdir -p "$APP_DIR" "$DB_DIR" "$WWW_DIR" "$ENV_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR" "$DB_DIR"
chmod 750 "$ENV_DIR"

echo "==> Caddy (official apt repo)"
if ! command -v caddy &>/dev/null; then
	curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
		| gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
	curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
		> /etc/apt/sources.list.d/caddy-stable.list
	apt-get update -y
	apt-get install -y caddy
fi

echo "==> enable automatic security updates"
dpkg-reconfigure -f noninteractive unattended-upgrades || true

echo "==> bootstrap complete."
echo "    Next: sync the code payload to $APP_DIR, drop the env file at $ENV_DIR/env,"
echo "    then run:  SITE_HOST=<host> sudo -E bash $APP_DIR/deploy/deploy.sh"
