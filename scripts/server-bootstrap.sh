#!/usr/bin/env bash
# First-time setup on a Ubuntu/Debian VPS. Run as root.
set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/fieldops}"
REPO_URL="${REPO_URL:?Set REPO_URL to your git clone URL}"

apt-get update
apt-get install -y ca-certificates curl git ufw

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a644 /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

mkdir -p "$DEPLOY_PATH"
if [[ ! -d "$DEPLOY_PATH/.git" ]]; then
  git clone "$REPO_URL" "$DEPLOY_PATH"
fi

mkdir -p "$DEPLOY_PATH/infra/nginx/certs" "$DEPLOY_PATH/infra/nginx/www" "$DEPLOY_PATH/infra/nginx/rendered"
if [[ ! -f "$DEPLOY_PATH/.env" ]]; then
  cp "$DEPLOY_PATH/deploy/env.production.example" "$DEPLOY_PATH/.env"
  echo "Edit $DEPLOY_PATH/.env before the first deploy."
fi

echo "Bootstrap complete. Next: fill .env, point DNS A records, then run a GitHub deploy or:"
echo "  cd $DEPLOY_PATH && bash scripts/render-nginx.sh && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d"
