#!/usr/bin/env bash
# Issue or renew a Let's Encrypt SAN certificate covering app + api + grafana.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${DOMAIN_APP:?}"
: "${DOMAIN_API:?}"
: "${DOMAIN_GRAFANA:?}"
: "${LETSENCRYPT_EMAIL:?}"
CERT_NAME="${CERT_NAME:-$DOMAIN_APP}"

cd "$ROOT"
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml run --rm --profile certs certbot certonly \
  --webroot -w /var/www/certbot \
  --email "$LETSENCRYPT_EMAIL" \
  --agree-tos --no-eff-email \
  --cert-name "$CERT_NAME" \
  -d "$DOMAIN_APP" \
  -d "$DOMAIN_API" \
  -d "$DOMAIN_GRAFANA"

bash "$ROOT/scripts/render-nginx.sh"
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml exec -T proxy nginx -s reload
echo "Certificate issued/renewed for $CERT_NAME"
