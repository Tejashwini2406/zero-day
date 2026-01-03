# 🚀 Zero-Day: How to Run

**Status**: ✅ Production Ready | **Last Tested**: January 3, 2026

---

## The Absolute Fastest Way (1 Command)

```bash
bash scripts/start_local_stack.sh
```

**That's it!** Everything starts automatically.

---

## Next: Open Grafana Dashboard

```
http://localhost:3000
Username: admin
Password: admin
```

Look for **"Zero-Day Demo Dashboard"** in the Dashboards menu.

---

## Run the Demos (Use 2 Terminals)

### Terminal 1: Normal Traffic
```bash
USE_KAFKA=false EVENTS_FILE=/home/wini/zero-day/events.jsonl bash scripts/demo_normal.sh
```
Watch the **Events/sec** panel spike in Grafana ⬆️

### Terminal 2: Attack Traffic
```bash
bash scripts/demo_attack.sh
```
Watch **Active Alerts** and **Attack Score** spike in Grafana 🚨

---

## What You'll See

### In Grafana Dashboard:
- **Events/sec** → Increases during demo
- **Active Alerts** → Jumps to 400+ during attack
- **Attack Score** → Goes from 0 to 50-70 during attack
- **Event Volume Graph** → Shows rate trend
- **Latency Graph** → Shows p95 processing time
- **Attack Score Graph** → Shows anomaly trend

### Color Coding:
- 🟢 **Green** = Normal/Safe
- 🟡 **Yellow** = Warning
- 🔴 **Red** = Critical

---

## Check Everything is Running

```bash
# See all services
docker-compose ps

# View metrics
curl http://localhost:8000/metrics | grep zero_day

# Test Prometheus
curl 'http://localhost:9090/api/v1/query?query=zero_day_events_total'

# Test Grafana
curl -u admin:admin http://localhost:3000/api/user
```

---

## If Something Breaks

### Grafana not loading?
```bash
docker-compose restart grafana
sleep 10
# Try http://localhost:3000 again
```

### No data in dashboard?
```bash
# Run attack demo again
bash scripts/demo_attack.sh

# Wait 5 seconds
sleep 5

# Refresh Grafana (F5 in browser)
```

### Services not starting?
```bash
# Full reset
docker-compose down -v
bash scripts/start_local_stack.sh
```

---

## Stop Everything

```bash
docker-compose stop
```

---

## Full Documentation

- **Quick Reference**: `QUICKSTART.md` (one-pager)
- **Complete Setup**: `SETUP.md` (everything explained)
- **Project Summary**: `PROJECT_DELIVERY.md` (full delivery report)

---

## What This Does

**Zero-Day** monitors for suspicious container/pod activity in real-time:

1. **Ingests Events** → Simulated security events (normal + attack traffic)
2. **Scores Anomalies** → ML-based threat scoring
3. **Alerts in Real-Time** → Detects attacks within seconds
4. **Visualizes** → Beautiful Grafana dashboards with color-coded alerts
5. **Stores Metrics** → Prometheus time-series database

---

## Architecture (Simple Version)

```
Your Demos (scripts) 
    ↓
File Generation (events.jsonl, attack_events.jsonl)
    ↓
Metrics Exporter (localhost:8000) ← Watches files
    ↓
Prometheus (localhost:9090) ← Scrapes metrics every 5 seconds
    ↓
Grafana Dashboard (localhost:3000) ← Displays beautiful graphs
```

---

## Performance

| Component | Time |
|-----------|------|
| Startup | <30 seconds |
| First metrics visible | <10 seconds |
| Dashboard fully loaded | <5 seconds |
| Alert latency | <1 second |

---

## That's Really All You Need!

1. ✅ Run: `bash scripts/start_local_stack.sh`
2. ✅ Open: http://localhost:3000 (admin/admin)
3. ✅ Demo: `bash scripts/demo_attack.sh`
4. ✅ Watch: Graphs spike in real-time 📈

---

**Questions?** See `SETUP.md` or `QUICKSTART.md`

**Ready to go!** 🎉
