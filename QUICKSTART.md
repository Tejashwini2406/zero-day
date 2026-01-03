# Zero-Day Quick Reference

## Start Project (One Command)
```bash
bash scripts/start_local_stack.sh
```
**Result**: Grafana, Prometheus, and metrics exporter running locally.

---

## Access Dashboards
| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | (no auth) |
| **Metrics Exporter** | http://localhost:8000/metrics | (no auth) |

---

## Run Demos (In Separate Terminals)

### Normal Traffic Demo
```bash
USE_KAFKA=false EVENTS_FILE=/home/wini/zero-day/events.jsonl bash scripts/demo_normal.sh
```
Generates 100 normal events. Watch **Events/sec** panel increase in Grafana.

### Attack Traffic Demo
```bash
bash scripts/demo_attack.sh
```
Generates 400 attack events. Watch **Active Alerts** and **Attack Score** spike in Grafana.

---

## Check Status

### All Services
```bash
docker-compose ps
```

### Metrics Being Exported
```bash
curl http://localhost:8000/metrics | grep zero_day
```

### Prometheus Scraping
```bash
curl 'http://localhost:9090/api/v1/query?query=zero_day_events_total'
```

### Grafana Health
```bash
curl -u admin:admin http://localhost:3000/api/user
```

---

## Cleanup

### Stop Services (Keep Data)
```bash
docker-compose stop
```

### Stop & Remove Volumes (Full Reset)
```bash
docker-compose down -v
```

### Remove Event Files
```bash
rm -f events*.jsonl attack_events.jsonl test_events.jsonl
```

---

## Common Tasks

### View Logs
```bash
docker-compose logs -f metrics_exporter
```

### Restart a Service
```bash
docker-compose restart grafana
```

### Check Dashboard
Open http://localhost:3000, go to Dashboards → Zero-Day Demo Dashboard

### Manually Import Dashboard
```bash
bash scripts/import_grafana_dashboard_local.sh
```

### Add Prometheus Datasource
```bash
bash scripts/add_prometheus_datasource_local.sh
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| **Grafana login not working** | Default is `admin:admin`. Restart: `docker-compose restart grafana` |
| **No data in dashboard** | Run demo script: `bash scripts/demo_attack.sh`, wait 5s, refresh |
| **Prometheus not scraping** | Check targets at http://localhost:9090/targets |
| **Exporter down** | Restart: `docker-compose restart metrics_exporter` |
| **Port already in use** | Kill process: `sudo lsof -i :3000` → `kill -9 <PID>` |

---

## Project Files

```
zero-day/
├── docker-compose.yml                    # Main service definitions
├── monitoring/
│   ├── grafana/
│   │   ├── demo_dashboard.json          # Grafana dashboard
│   │   └── README.md                    # Grafana docs
│   ├── prometheus/
│   │   └── prometheus.yml               # Prometheus config
│   └── metrics_exporter/
│       ├── Dockerfile                   # Exporter image
│       └── metrics_exporter.py          # Metrics logic
├── scripts/
│   ├── start_local_stack.sh             # Start all services
│   ├── demo_normal.sh                   # Normal traffic demo
│   ├── demo_attack.sh                   # Attack traffic demo
│   ├── import_grafana_dashboard_local.sh
│   └── add_prometheus_datasource_local.sh
└── SETUP.md                             # Full documentation
```

---

**Status**: ✅ Production Ready
**Last Tested**: January 3, 2026
