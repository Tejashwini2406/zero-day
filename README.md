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
