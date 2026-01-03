#!/usr/bin/env bash
set -euo pipefail
# Imports monitoring/grafana/demo_dashboard.json into Grafana using API
if [[ -z "${GRAFANA_URL:-}" || -z "${GRAFANA_API_KEY:-}" ]]; then
  echo "Set GRAFANA_URL and GRAFANA_API_KEY environment variables"
  echo "Example: export GRAFANA_URL=https://grafana.example.com; export GRAFANA_API_KEY=ey..."
  exit 1
fi

DASHFILE="$(cd "$(dirname "$0")" && pwd)/../monitoring/grafana/demo_dashboard.json"
if [ ! -f "$DASHFILE" ]; then
  echo "Dashboard file not found: $DASHFILE"
  exit 1
fi

echo "Importing dashboard $DASHFILE to $GRAFANA_URL"
curl -sS -H "Authorization: Bearer $GRAFANA_API_KEY" -H "Content-Type: application/json" \
  -X POST "$GRAFANA_URL/api/dashboards/db" --data-binary "@$DASHFILE" \
  || { echo "Import failed"; exit 2; }

echo "Import complete. Open Grafana to verify the dashboard."

exit 0
