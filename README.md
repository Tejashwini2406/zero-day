
# Zero-Day PoC (Zero-Day Detection Prototype)

This repository contains a proof-of-concept zero-day detection pipeline, monitoring stack, dashboards, and report artifacts used for the final deliverable.

**Contents**
- `infra/` : Kubernetes manifests for the cluster (monitoring, exporter, Grafana, Prometheus, etc.).
- `scripts/` : Helper and demo scripts for running the PoC and capturing artifacts.
- `report/` : Generated DOCX/JSON and markdown reports and dashboard JSON.
- `paper/` : IEEE-format paper source (LaTeX) and build instructions.

## Prerequisites
- `kubectl` configured for your Minikube/cluster
- `docker` (for building images locally, if needed)
- `pandoc` (optional, for converting markdown -> DOCX)
- `pdflatex` or `latexmk` (optional, to compile the IEEE paper)
- `jq`, `curl` (used in scripts)

## Quick Deploy
1. Apply infrastructure and monitoring manifests:

```bash
kubectl apply -f infra/k8s/monitoring/prometheus-config.yaml
kubectl apply -f infra/k8s/monitoring/alert-exporter.yaml
kubectl apply -f infra/k8s/monitoring/grafana-deploy.yaml
# other infra manifests (graph-builder, inference, etc.)
kubectl apply -f infra/k8s
```

2. Build images (if you want to rebuild locally):

```bash
# Example (from repo root):
docker build -t alert-exporter:local -f infra/monitoring/alert_exporter/Dockerfile infra/monitoring/alert_exporter
```

3. Start demo pipeline (file-mode PoC):

```bash
bash scripts/demo_full.sh
```

## How to verify monitoring and dashboards (show)
1. Port-forward Prometheus and Grafana locally:

```bash
kubectl -n ml port-forward svc/prometheus 9090:9090 >/dev/null 2>&1 &
kubectl -n ml port-forward svc/grafana 3000:3000 >/dev/null 2>&1 &
kubectl -n ml port-forward svc/alert-exporter 8000:8000 >/dev/null 2>&1 &
```

2. Query the exporter directly:

```bash
curl -s http://127.0.0.1:8000/metrics | egrep 'zd_windows_count|zd_alerts_count'
```

3. Query Prometheus for the metric:

```bash
curl -s 'http://127.0.0.1:9090/api/v1/query?query=zd_windows_count' | jq
```

4. Open Grafana: `http://127.0.0.1:3000` (default `admin:admin123`).
   Dashboard UID: `zerodaymetrics`.

## Capture screenshots and export
Use the helper script to capture Grafana dashboard panels and convert markdown reports to DOCX (requires `pandoc`):

```bash
chmod +x scripts/capture_grafana.sh scripts/generate_docx.sh
scripts/capture_grafana.sh      # captures panels into report/*.png
scripts/generate_docx.sh report/4_MONITORING.md "report/4. MONITORING.docx"
```

## Paper (IEEE)
The LaTeX source for the IEEE-format paper is in `paper/zero_day_ieee.tex`. See `paper/README.md` to build a PDF.

## Reproduce & Handoff
- See `REPRODUCE.md` and `JURY_GUIDE.md` in `report/` for step-by-step reproduction and judging notes.

If you want, I can: (a) run the capture script and embed the screenshot into the monitoring report, (b) compile the LaTeX paper to PDF. Tell me which you'd like me to run now.
# Zero-Day Detection & Mitigation Framework for Kubernetes (PoC)

A production-oriented proof-of-concept for detecting and mitigating zero-day attacks in Kubernetes clusters using temporal graph neural networks, anomaly detection, and safe automated containment.

## Key Components

- **Infrastructure**: Minikube with Istio, Cilium, Kubernetes audit logging.
- **Telemetry**: Kafka + OpenTelemetry Collector + Fluent Bit for multi-source event ingestion.
- **Graph Building**: Sessionization and temporal graph construction (Parquet outputs).
- **ML Baselines**: Autoencoder, LSTM-AE, and DeepLog-style anomaly detectors.
- **TGNN**: Temporal Graph Neural Network using PyTorch + PyG.
- **Inference**: REST API for scoring and emitting Alert CRs to Kubernetes.
- **Containment**: Operator/controller to safely apply NetworkPolicies, pod eviction, traffic isolation.
- **Monitoring**: Prometheus + Grafana + ClickHouse for observability.

## Quick Start

```bash
# One-command setup (requires docker, kubectl, minikube, helm, istioctl)
bash scripts/quick_start.sh
```

Or step-by-step:
```bash
make setup-minikube        # Start cluster with Istio + Cilium
make setup-telemetry       # Deploy Kafka, OTel, Fluent Bit
make build-images          # Build container images
make deploy-all            # Deploy all services
make setup-monitoring      # Deploy Prometheus/Grafana/ClickHouse
```

See `INTEGRATION_GUIDE.md` for detailed operational steps, testing, and troubleshooting.

## Project Structure

```
zero-day/
├── infra/                  # Infrastructure setup and Kubernetes manifests
│   ├── minikube/          # Local cluster setup scripts
│   ├── k8s/               # Kubernetes manifests (namespaces, RBAC, policies, audit)
│   │   ├── otel/          # OpenTelemetry Collector
│   │   ├── fluentbit/     # Fluent Bit log forwarding
│   │   ├── kafka/         # Strimzi Kafka cluster
│   │   ├── graph-builder/ # Graph builder deployment
│   │   ├── ml/            # ML training job and inference service
│   │   └── containment/   # Containment operator
│   └── terraform/         # (Placeholder) Cloud provider IaC
├── graph_builder/         # Temporal graph builder microservice
│   ├── src/               # Sessionization, graph building, Parquet output
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── ml/                    # ML baselines and training pipeline
│   ├── src/
│   │   └── ml_pipeline/
│   │       ├── data.py         # Synthetic data generation
│   │       ├── models.py       # Autoencoder, LSTM-AE, DeepLog
│   │       ├── train.py        # Training CLI
│   │       └── inference.py    # Inference service with Alert CR emission
│   ├── Dockerfile
│   ├── Dockerfile.inference
│   └── requirements.txt
├── containment/           # Containment operator (Go, controller-runtime)
│   ├── operator.go        # Skeleton operator for safe containment actions
│   ├── crd.yaml           # Containment CRD definition
│   ├── Dockerfile
│   └── go.mod
├── scripts/
│   ├── smoke_test.sh      # Smoke tests for deployed services
│   ├── quick_start.sh     # Automated one-shot setup
│   └── (validation/attack playbooks - TBD)
├── Makefile               # Build and deployment helpers
├── INTEGRATION_GUIDE.md   # Complete operational guide
└── README.md              # This file
```

## Features

- **Multi-source telemetry**: eBPF syscalls, network flows, Istio L7 traces, Kubernetes audit logs
- **Streaming pipeline**: Kafka → graph builder → Parquet snapshots
- **Anomaly detection**: Baseline models (AE, LSTM-AE, DeepLog) + TGNN for graph patterns
- **Explainability**: XAI integration (SHAP, GNNExplainer) for interpretable alerts
- **Safe containment**: Policy-driven actions (NetworkPolicy, pod eviction, traffic control) with approval workflow
- **Observability**: Prometheus metrics, Grafana dashboards, Jaeger traces, structured logs
- **Reproducibility**: Fully scripted, containerized, Kubernetes-native manifests

## Technology Stack

- **Orchestration**: Kubernetes / Minikube / GKE / EKS / AKS
- **Service Mesh**: Istio with mTLS
- **eBPF**: Cilium/Hubble
- **Message Bus**: Apache Kafka (Strimzi)
- **Storage**: Parquet (graphs), ClickHouse/Elasticsearch (telemetry)
- **ML**: PyTorch, PyTorch Geometric, scikit-learn, SHAP
- **Containment**: Go (controller-runtime), Kubernetes operators
- **Monitoring**: Prometheus, Grafana, OpenTelemetry, Jaeger

## Testing & Validation

### Local (no cluster)
```bash
cd graph_builder && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m graph_builder.synthetic_generator --out events.jsonl --count 1000
python -m graph_builder.main file --input-file events.jsonl --out-dir ./graphs
```

### ML Baseline Training
```bash
cd ml && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash run_train.sh
```

### In-Cluster
See `INTEGRATION_GUIDE.md` for red-team attack simulations, MITRE ATT&CK mapping, and model evaluation.

## Next Steps

1. **Complete TGNN**: Add PyG tensor conversion and full temporal graph neural network
2. **XAI expansion**: GNNExplainer, Integrated Gradients for node/edge attributions
3. **Attack playbooks**: Container escape, privilege escalation, lateral movement scenarios
4. **Production dashboards**: Real-time anomaly counts, model metrics, containment action history
5. **Advanced containment**: VirtualService blackholing, PodDisruptionBudgets, capability restrictions
6. **Cloud IaC**: Terraform modules for GKE/EKS/AKS deployment

## Disclaimer

**Research/PoC only**: This framework is designed for controlled lab environments and educational purposes.
- Deploy only in isolated, air-gapped Kubernetes clusters
- Test containment actions in staging before any production use
- Anomaly thresholds require careful tuning per environment
- Attack simulations must be approved and conducted in dedicated test environments

---

For detailed operational instructions, see `INTEGRATION_GUIDE.md`. For component-specific guidance, check READMEs in `graph_builder/`, `ml/`, and `containment/` directories.
