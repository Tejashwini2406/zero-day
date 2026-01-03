#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)/..

echo "Starting local stack with Docker Compose..."
docker-compose up -d

echo "Waiting for Grafana to become ready (http://localhost:3000)..."
for i in {1..60}; do
  status=$(curl -sS -o /dev/null -w "%{http_code}" http://localhost:3000/api/health || true)
  if [ "$status" = "200" ]; then
    echo "Grafana is ready"
    break
  fi
  sleep 2
done

echo "Importing dashboard using basic auth (admin/admin -> admin password set to 'admin')"
bash "$HERE/scripts/import_grafana_dashboard_local.sh" || echo "Dashboard import failed; you can import manually using scripts/import_grafana_dashboard.sh"

echo "Local stack started."
