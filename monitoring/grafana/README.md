# Zero-Day Grafana Demo Dashboard

Import the dashboard and run the demo scripts to observe normal vs attack traffic.

Import
- Ensure `GRAFANA_URL` and `GRAFANA_API_KEY` are set, then:
```bash
bash scripts/import_grafana_dashboard.sh
```

Quick demo
- Run normal traffic (in another terminal):
```bash
bash scripts/demo_normal.sh
```
- Run attack traffic:
```bash
bash scripts/demo_attack.sh
```

What to look for
- `Events/sec`: watch for spikes in event volume when attack script runs.
- `Active Alerts`: should increase when attacks are generated.
- `Processing Latency (p95 ms)`: check for degradation under load.
- `Attack Score`: higher values indicate suspicious activity; thresholds color-code severity.

Metrics expected
- `zero_day_events_total` — total events counter
- `zero_day_attack_alerts_total` — alerts counter
- `graph_builder_processing_duration_seconds_bucket` — processing histogram
- `zero_day_attack_score` — attack scoring gauge

If your environment uses a different Prometheus datasource name, update the dashboard variable `DS_PROM` after import.
