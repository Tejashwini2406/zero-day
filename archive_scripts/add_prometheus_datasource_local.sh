#!/usr/bin/env bash
set -euo pipefail
GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
USER=${GRAFANA_USER:-admin}
PASS=${GRAFANA_PASS:-admin}

cat <<EOF > /tmp/prom_ds.json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy",
  "isDefault": true
}
EOF

echo "Creating Prometheus datasource in Grafana ($GRAFANA_URL)"
curl -sS -u ${USER}:${PASS} -H "Content-Type: application/json" -X POST ${GRAFANA_URL}/api/datasources --data-binary @/tmp/prom_ds.json || { echo "Failed to create datasource"; exit 1; }

echo "Datasource created."
