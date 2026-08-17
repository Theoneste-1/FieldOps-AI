#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

: "${DOMAIN_APP:?Set DOMAIN_APP in .env}"
: "${DOMAIN_API:?Set DOMAIN_API in .env}"
: "${DOMAIN_GRAFANA:?Set DOMAIN_GRAFANA in .env}"
CERT_NAME="${CERT_NAME:-$DOMAIN_APP}"

mkdir -p "$ROOT/infra/nginx/rendered"
SRC="$ROOT/infra/nginx/templates/http.conf"
CERT_DIR="${LETSENCRYPT_LIVE:-$ROOT/infra/nginx/certs/live/$CERT_NAME}"
if [[ -f "$CERT_DIR/fullchain.pem" && -f "$CERT_DIR/privkey.pem" ]]; then
  SRC="$ROOT/infra/nginx/templates/https.conf"
  echo "TLS files found — rendering HTTPS nginx config"
else
  echo "No TLS files yet — rendering HTTP nginx config (use this to obtain certificates)"
fi

sed \
  -e "s/__DOMAIN_APP__/${DOMAIN_APP}/g" \
  -e "s/__DOMAIN_API__/${DOMAIN_API}/g" \
  -e "s/__DOMAIN_GRAFANA__/${DOMAIN_GRAFANA}/g" \
  -e "s/__CERT_NAME__/${CERT_NAME}/g" \
  "$SRC" > "$ROOT/infra/nginx/rendered/default.conf"

echo "Wrote $ROOT/infra/nginx/rendered/default.conf"
