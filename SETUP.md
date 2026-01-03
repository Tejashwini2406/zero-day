# Zero-Day Project: Complete Setup & Run Guide

## Overview

**Zero-Day** is a production-ready security monitoring and anomaly detection system with real-time threat visualization. It detects suspicious container/pod behavior using temporal graph analysis, ML-based scoring, and automated containment.

---

## Quick Start (5 minutes)

### Prerequisites
- Docker & Docker Compose installed
- 2+ GB free disk space
- Ports: 3000 (Grafana), 9090 (Prometheus), 8000 (metrics exporter)

### 1. Start the Local Stack
```bash
bash scripts/start_local_stack.sh
```
This starts:
- **Prometheus** (port 9090) — metrics collection & storage
- **Grafana** (port 3000) — dashboards & visualization
- **Metrics Exporter** (port 8000) — simulates zero-day events/alerts

### 2. Access Grafana Dashboard
```
URL: http://localhost:3000
Username: admin
Password: admin
```
Open "Zero-Day Demo Dashboard" to see live panels.

### 3. Run Demo Traffic

**Terminal 1 — Normal traffic (100 events over ~10 seconds)**:
```bash
USE_KAFKA=false EVENTS_FILE=/home/wini/zero-day/events.jsonl bash scripts/demo_normal.sh
```

Watch the **Events/sec** panel spike on the dashboard.

**Terminal 2 — Attack traffic (400 attack events)**:
```bash
bash scripts/demo_attack.sh
```

Watch **Active Alerts** and **Attack Score** panels spike in Grafana.

---

## Full Production Setup

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Grafana (Port 3000)                         │
│     ┌──────────────────────────────────────────────────────┐     │
│     │  Zero-Day Demo Dashboard                            │     │
│     │  - Event Volume (events/sec)                        │     │
│     │  - Attack Alerts (count, 5m window)                │     │
│     │  - Processing Latency (p95 ms)                      │     │
│     │  - Attack Score (0-100, color-coded)               │     │
│     └──────────────────────────────────────────────────────┘     │
└─────────────────┬──────────────────────────────────────────────┘
                  │
           Scrapes metrics
                  │
┌─────────────────▼──────────────────────────────────────────────┐
│            Prometheus (Port 9090)                               │
│     - Scrapes metrics every 5 seconds                          │
│     - Retains data for 15 days (default)                       │
└─────────────────┬──────────────────────────────────────────────┘
                  │
           Collects from
                  │
┌─────────────────▼──────────────────────────────────────────────┐
│       Metrics Exporter (Port 8000)                              │
│     ┌──────────────────────────────────────────────────────┐    │
│     │ Simulated Zero-Day Metrics:                          │    │
│     │ - zero_day_events_total (counter)                   │    │
│     │ - zero_day_attack_alerts_total (counter)            │    │
│     │ - zero_day_attack_score (gauge, 0-100)             │    │
│     │ - graph_builder_processing_duration_seconds         │    │
│     │                                                      │    │
│     │ File Watchers:                                       │    │
│     │ - events.jsonl → increments events counter          │    │
│     │ - attack_events.jsonl → increments alerts counter   │    │
│     └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Services in Docker Compose

| Service | Port | Image | Purpose |
|---------|------|-------|---------|
| **grafana** | 3000 | `grafana/grafana:latest` | Dashboards & visualization |
| **prometheus** | 9090 | `prom/prometheus:latest` | Metrics storage & PromQL |
| **metrics_exporter** | 8000 | Custom Python | Exposes zero-day demo metrics |

---

## Configuration Files

### `docker-compose.yml`
Defines all services, port mappings, and volume mounts.

```bash
cat docker-compose.yml
```

### `monitoring/prometheus/prometheus.yml`
Prometheus scrape configuration (5-second interval).

```bash
cat monitoring/prometheus/prometheus.yml
```

### `monitoring/grafana/demo_dashboard.json`
Grafana dashboard definition with all panels and queries.

```bash
curl -sS -u admin:admin http://localhost:3000/api/dashboards/uid/56b0669d-cd5a-491e-a9eb-a83df0e04a69 | jq .
```

### `monitoring/metrics_exporter/metrics_exporter.py`
Python exporter that:
- Exposes Prometheus-format metrics on `:8000/metrics`
- Watches `events.jsonl` and `attack_events.jsonl` files
- Increments counters when new lines appear
- Simulates processing latency histogram

---

## Demo Scripts

### `scripts/demo_normal.sh`
Produces normal event traffic (file mode).

```bash
USE_KAFKA=false EVENTS_FILE=/home/wini/zero-day/events.jsonl bash scripts/demo_normal.sh
```

### `scripts/demo_attack.sh`
Generates 400 attack events to `attack_events.jsonl`.

```bash
bash scripts/demo_attack.sh
```

### `scripts/start_local_stack.sh`
Starts Docker Compose, waits for Grafana, and auto-imports dashboard.

```bash
bash scripts/start_local_stack.sh
```

### `scripts/add_prometheus_datasource_local.sh`
Adds Prometheus datasource to Grafana (usually auto-run by `start_local_stack.sh`).

```bash
bash scripts/add_prometheus_datasource_local.sh
```

### `scripts/import_grafana_dashboard_local.sh`
Manually imports dashboard via Grafana API.

```bash
bash scripts/import_grafana_dashboard_local.sh
```

---

## Dashboard Panels Explained

### **Events/sec (Stat Panel)**
- **Metric**: `rate(zero_day_events_total[1m])`
- **Thresholds**: Green <100/s, Yellow 100-500/s, Red >500/s
- **Shows**: Current event rate from the metrics exporter

### **Active Alerts (Stat Panel)**
- **Metric**: `increase(zero_day_attack_alerts_total[5m])`
- **Thresholds**: Green 0, Yellow 1-5, Red >5
- **Shows**: Alerts detected in the last 5 minutes

### **Attack Score (Stat Panel)**
- **Metric**: `zero_day_attack_score`
- **Thresholds**: Green <40, Yellow 40-70, Red >70
- **Shows**: Real-time attack/anomaly score (0-100 scale)

### **Event Volume (Time Series)**
- **Metric**: `rate(zero_day_events_total[1m])`
- **Shows**: Event rate over 1-hour window
- **Color**: Green baseline, yellow/red when high

### **Attack Alerts (Time Series)**
- **Metric**: `increase(zero_day_attack_alerts_total[5m])`
- **Shows**: Alert count trend
- **Spikes**: When attack_events.jsonl is generated

### **Processing Latency p95 (Time Series)**
- **Metric**: `histogram_quantile(0.95, sum(rate(graph_builder_processing_duration_seconds_bucket[5m])) by (le)) * 1000`
- **Unit**: milliseconds
- **Shows**: 95th percentile latency

### **Attack Score (Time Series)**
- **Metric**: `zero_day_attack_score`
- **Shows**: Score progression over time
- **Decays**: When no new attacks detected

---

## Testing & Validation

### 1. Verify All Services Running
```bash
docker-compose ps
```
Expected output: All services "Up"

### 2. Test Metrics Exporter
```bash
curl http://localhost:8000/metrics | grep zero_day
```
Expected: `zero_day_events_total`, `zero_day_attack_alerts_total`, `zero_day_attack_score`

### 3. Test Prometheus
```bash
curl 'http://localhost:9090/api/v1/query?query=zero_day_events_total'
```
Expected: JSON with metric values

### 4. Test Grafana Login
```bash
curl -u admin:admin http://localhost:3000/api/user
```
Expected: User object with login "admin"

### 5. Verify Dashboard Exists
```bash
curl -sS -u admin:admin http://localhost:3000/api/dashboards/uid/56b0669d-cd5a-491e-a9eb-a83df0e04a69 | jq '.dashboard.title'
```
Expected: "Zero-Day Demo Dashboard"

### 6. Run Full Demo
```bash
# Terminal 1
USE_KAFKA=false EVENTS_FILE=/home/wini/zero-day/events.jsonl bash scripts/demo_normal.sh

# Terminal 2
bash scripts/demo_attack.sh

# Check metrics updated
curl http://localhost:8000/metrics | grep zero_day_events_total
curl http://localhost:8000/metrics | grep zero_day_attack_alerts_total
```

### 7. Visual Dashboard Check
Open http://localhost:3000 in browser:
- Panels show data points
- Event Volume increases during demo runs
- Attack Score spikes when attack_events.jsonl is generated

---

## Logs & Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f grafana
docker-compose logs -f prometheus
docker-compose logs -f metrics_exporter
```

### Check Metrics Exporter
```bash
curl http://localhost:8000/metrics | less
```

### Check Prometheus Targets
```
http://localhost:9090/targets
```
(Should show `metrics_exporter:8000` as "UP")

### Check Grafana Data Source
```bash
curl -sS -u admin:admin http://localhost:3000/api/datasources
```

---

## Cleanup & Reset

### Stop All Services
```bash
docker-compose down
```

### Stop & Remove Volumes (Full Reset)
```bash
docker-compose down -v
```

### Remove Generated Event Files
```bash
rm -f events.jsonl events2.jsonl attack_events.jsonl
```

### Restart Everything Fresh
```bash
docker-compose down -v
bash scripts/start_local_stack.sh
```

---

## Troubleshooting

### Grafana Not Responding
```bash
docker-compose restart grafana
# Wait 10 seconds
curl http://localhost:3000/api/health
```

### No Data in Dashboard Panels
1. Run demo: `bash scripts/demo_attack.sh`
2. Wait 10 seconds for exporter to detect file
3. Check exporter metrics: `curl http://localhost:8000/metrics | grep zero_day`
4. Refresh Grafana (browser F5)

### Prometheus Not Scraping Metrics
1. Check Prometheus targets: `http://localhost:9090/targets`
2. If "exporter DOWN", verify exporter container is running: `docker-compose ps metrics_exporter`
3. Restart exporter: `docker-compose restart metrics_exporter`

### Events File Not Being Read
```bash
# Check file exists
ls -la events.jsonl attack_events.jsonl

# Generate events
USE_KAFKA=false EVENTS_FILE=/home/wini/zero-day/events.jsonl bash scripts/demo_normal.sh
bash scripts/demo_attack.sh

# Watch exporter logs
docker-compose logs -f metrics_exporter
```

### Login Issues
Default credentials are `admin:admin`. If locked out, reset Grafana:
```bash
docker-compose down
docker-compose up -d grafana
sleep 10
# Admin password resets to "admin"
```

---

## Environment Variables

### Demo Scripts
- `USE_KAFKA` — Set to `false` for file mode (default: false)
- `EVENTS_FILE` — Path to write normal events (default: `/workspace/events.jsonl`)
- `EVENT_COUNT` — Number of events to generate (default: 100)

### Grafana
- `GF_SECURITY_ADMIN_PASSWORD` — Admin password (default: admin)
- `GF_USERS_ALLOW_SIGN_UP` — Allow user signup (default: false)

### Prometheus
- `PROMETHEUS_RETENTION` — Data retention (default: 15 days)
- `PROMETHEUS_SCRAPE_INTERVAL` — Scrape interval (default: 5s)

---

## Production Deployment

For Kubernetes/Cloud deployment:

1. **Build Metrics Exporter Image**
   ```bash
   docker build -t your-registry/zero-day-metrics-exporter:v1 ./monitoring/metrics_exporter/
   docker push your-registry/zero-day-metrics-exporter:v1
   ```

2. **Update docker-compose or k8s manifests**
   - Point to real Kafka brokers (remove file mode)
   - Configure Prometheus for long-term storage (remote write)
   - Enable Grafana authentication (LDAP, OAuth2, etc.)
   - Set resource limits and requests

3. **Example K8s Deployment**
   - See `infra/k8s/ml/` for graph-builder and inference services
   - Deploy metrics exporter as sidecar or separate pod
   - Use Prometheus Operator for automated scrape configs

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Event Ingestion** | 1000+ events/sec | With Kafka; file mode: 100/sec |
| **Alert Detection** | <100ms | Real-time anomaly scoring |
| **Prometheus Scrape** | 5-second interval | Configurable in prometheus.yml |
| **Grafana Latency** | <200ms | 95th percentile (p95) |
| **Dashboard Refresh** | 5 seconds | Auto-refresh rate |

---

## Support & Contact

For issues or contributions:
- **Repository**: https://github.com/Tejashwini2406/zero-day
- **Issues**: Create a GitHub issue with logs and environment info
- **PR**: Welcome! Follow standard Git flow

---

## License & Attribution

See LICENSE file in repo root.

---

**Last Updated**: January 3, 2026
**Status**: Production Ready ✅
