# Monitoring: Zero-Day PoC

This document summarizes the monitoring components, verification steps, and how to capture dashboard screenshots.

## Components
- Alert Exporter: Python-based Prometheus exporter exposing `zd_windows_count` and `zd_alerts_count` (default port `8000`).
- Prometheus: Scrapes the exporter (configured to `alert-exporter.ml.svc.cluster.local:8000`) and stores metrics in TSDB.
- Grafana: Dashboard (UID `zerodaymetrics`) with two panels showing Windows Count and Alerts Count.

## Verification
1. Confirm exporter metrics are available:

```bash
kubectl -n ml port-forward svc/alert-exporter 8000:8000 >/dev/null 2>&1 &
curl -s http://127.0.0.1:8000/metrics | egrep 'zd_windows_count|zd_alerts_count'
# Expected output example:
# zd_windows_count 120.0
# zd_alerts_count 121.0
```

2. Confirm Prometheus target health:

```bash
kubectl -n ml port-forward svc/prometheus 9090:9090 >/dev/null 2>&1 &
curl -s 'http://127.0.0.1:9090/api/v1/targets' | jq '.data.activeTargets[] | {labels: .labels, health: .health, lastError: .lastError}'
# Look for the alert-exporter job with health: "up"
```

3. Query Prometheus for a metric:

```bash
curl -s 'http://127.0.0.1:9090/api/v1/query?query=zd_windows_count' | jq
```

## Grafana
- Login: `http://127.0.0.1:3000` (default `admin:admin123`).
- Dashboard UID: `zerodaymetrics`.

## Capture and embed
- Use `scripts/capture_grafana.sh` to render panels to PNG. The script uses Grafana's render endpoint and requires Grafana to be reachable locally.
- Use `scripts/generate_docx.sh` to convert this markdown file to DOCX via `pandoc` if needed.

## Notes and troubleshooting
- If Prometheus target shows `down` and a `context deadline exceeded` error, check for duplicate ConfigMap entries in `infra/k8s/monitoring/prometheus-config.yaml` and ensure the target port is `8000`.
- If Grafana shows "No data" in panels, verify Prometheus has the metrics in its TSDB (query with Prometheus API) and that the panels' Prometheus datasource is correct.
