#!/usr/bin/env bash
set -euo pipefail
# Import the demo dashboard using basic auth (admin/admin)
GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
GRAPH_FILE="$(cd "$(dirname "$0")" && pwd)/../monitoring/grafana/demo_dashboard.json"

if [ ! -f "$GRAPH_FILE" ]; then
  echo "Dashboard file not found: $GRAPH_FILE"
  exit 1
fi

echo "Importing $GRAPH_FILE to $GRAFANA_URL with basic auth admin:admin"
curl -sS -u admin:admin -H "Content-Type: application/json" -X POST "$GRAFANA_URL/api/dashboards/db" --data-binary "@$GRAPH_FILE" || {
  echo "Import failed"
  exit 2
}

echo "Import complete. Login at $GRAFANA_URL (admin/admin)."
