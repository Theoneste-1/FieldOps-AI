#!/usr/bin/env bash
# Pull published images and restart the production stack.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -n "${GHCR_TOKEN:-}" ]]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "${GHCR_USERNAME:-github}" --password-stdin
fi

bash "$ROOT/scripts/render-nginx.sh"
docker compose --env-file "$ROOT/.env" -f docker-compose.prod.yml pull
docker compose --env-file "$ROOT/.env" -f docker-compose.prod.yml up -d --remove-orphans

echo "Waiting for API health..."
for i in $(seq 1 30); do
  if docker compose --env-file "$ROOT/.env" -f docker-compose.prod.yml exec -T api \
      python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" >/dev/null 2>&1; then
    echo "API is healthy"
    break
  fi
  sleep 2
done

docker compose --env-file "$ROOT/.env" -f docker-compose.prod.yml ps
