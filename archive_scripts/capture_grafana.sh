#!/usr/bin/env bash
# Capture Grafana dashboard panels to PNG using Grafana render API.
# Usage: ./scripts/capture_grafana.sh [grafana_host] [user] [password]
# Defaults: grafana_host=http://127.0.0.1:3000, user=admin, password=admin123

GRAFANA_HOST=${1:-http://127.0.0.1:3000}
GRAFANA_USER=${2:-admin}
GRAFANA_PASS=${3:-admin123}
OUTDIR=${4:-report}

mkdir -p "$OUTDIR"

for PANEL in 1 2; do
  OUT="$OUTDIR/grafana_panel_${PANEL}.png"
  echo "Rendering grafana panel $PANEL -> $OUT"
  curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" \
    "$GRAFANA_HOST/render/d-solo/zerodaymetrics/zeroday-poc-metrics?panelId=$PANEL&width=1000&height=400&from=now-1h&to=now" \
    -o "$OUT"
  if [ $? -ne 0 ]; then
    echo "Failed to capture panel $PANEL"
  fi
done

echo "Captured files in $OUTDIR"
