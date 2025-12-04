# End-to-End Integration Guide

This document describes the complete flow from telemetry ingestion through to containment actions.

## Architecture flow

```
Kubernetes Cluster
  ↓
eBPF + Audit Logs
  ↓
Fluent Bit → Kafka (telemetry.logs topic)
  ↓
graph-builder (Deployment) reads from Kafka
  ↓
Parquet window outputs (/data/graphs/)
  ↓
ML Trainer (CronJob) reads Parquet
  ↓
Trains Autoencoder/LSTM-AE models
  ↓
Models saved to volume
  ↓
Inference Service (Deployment) loads models
  ↓
Scores incoming windows, emits Alert CRs
  ↓
Containment Operator watches Alert CRs
  ↓
Applies safe actions: NetworkPolicy, eviction, etc.
```

## Prerequisites

- Minikube with 3 nodes, 8GB RAM, 4 CPUs minimum.
- Docker/buildkit for building container images.
- kubectl, helm, istioctl installed.
- Python 3.11+ with virtualenv for local training/testing.

## Step-by-step deployment

### 1. Spin up Minikube and base infra

```bash
make setup-minikube
make apply-manifests
```

### 2. Deploy telemetry stack (Kafka, OTel, Fluent Bit)

```bash
make setup-telemetry
```

Wait for Kafka pods to be ready:
```bash
kubectl -n kafka get pods
kubectl -n kafka get kafka
```

### 3. Deploy monitoring (Prometheus, Grafana, ClickHouse)

```bash
make setup-monitoring
```

Access Grafana via port-forward:
```bash
kubectl -n monitoring port-forward svc/kube-prometheus-grafana 3000:80
# Login with admin / prom-operator
```

### 4. Build container images

```bash
make build-images
```

Or build individually:
```bash
docker build -t graph-builder:latest graph_builder/
docker build -t ml:latest ml/
docker build -t inference:latest -f ml/Dockerfile.inference .
docker build -t containment-operator:latest containment/
```

### 5. Load images into Minikube

```bash
# If using docker driver, images are automatically available
# Otherwise, use minikube image load:
minikube image load graph-builder:latest
minikube image load ml:latest
minikube image load inference:latest
minikube image load containment-operator:latest
```

### 6. Deploy graph-builder, ML training, inference, and operator

```bash
make deploy-graph-builder
make deploy-ml
make deploy-operator
```

### 7. Deploy sample app to generate logs

```bash
kubectl apply -f infra/k8s/sample-app/sample-app.yaml
```

### 8. Verify components

```bash
# Check graph-builder
kubectl -n ml get pods -l app=graph-builder
kubectl -n ml logs -f deploy/graph-builder

# Check inference service
kubectl -n ml get pods -l app=inference
kubectl -n ml logs -f deploy/inference-service

# Check containment operator
kubectl -n quarantine get pods -l app=containment-operator
kubectl -n quarantine logs -f deploy/containment-operator

# Check if alerts are created
kubectl get containments -A
```

## Testing the flow

### 1. Generate synthetic events

Run from `graph_builder/` directory:
```bash
python -m graph_builder.synthetic_generator --out test_events.jsonl --count 500
```

### 2. Test graph-builder locally (file mode)

```bash
cd graph_builder
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m graph_builder.main file --input-file test_events.jsonl --out-dir ./test_graphs --window-size 60 --step 30
```

### 3. Check Parquet outputs

```bash
python -c "import pandas as pd; print(pd.read_parquet('./test_graphs/window_*.nodes.parquet'))"
```

### 4. Train ML baseline locally

```bash
cd ml
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash run_train.sh  # Trains AE and LSTM-AE
ls models/  # Check trained model artifacts
```

### 5. Test inference service

Port-forward the inference service:
```bash
kubectl -n ml port-forward svc/inference 8080:8080
```

Score a window via HTTP:
```bash
curl -X POST http://localhost:8080/score \
  -H "Content-Type: application/json" \
  -d '{
    "pod_name": "svc-1",
    "namespace": "dev",
    "features": [0.1, -0.2, 0.3, ..., 0.05]
  }'
```

## Next steps

1. **Integrate PyG for TGNN**: Add a converter from node/edge Parquet tables to PyTorch Geometric tensors, then train the TGNN model.
2. **Add XAI**: Integrate SHAP or GNNExplainer to explain model decisions.
3. **Red-team tests**: Deploy attack simulators and validate detection rates.
4. **Dashboards**: Build Grafana panels for anomaly rates, model metrics, and containment action counts.
5. **Operators**: Enhance the containment operator to safely apply VirtualService blackholing, PodDisruptionBudgets, and resource throttling.

## Troubleshooting

- **Kafka not ready**: Check `kubectl -n kafka get pods` and wait for broker to start.
- **Graph-builder pod errors**: Check `kubectl -n ml logs deploy/graph-builder` for Kafka connection issues.
- **Inference service crashing**: Ensure `MODEL_PATH` environment variable points to a valid trained model, or check for missing dependencies.
- **Alert CRs not created**: Verify inference service has RBAC permissions to create Containments (check `infra/k8s/ml/inference-rbac.yaml`).

## References

- Graph builder: `graph_builder/README.md`
- ML baselines: `ml/README.md`
- Containment CRD: `containment/crd.yaml`
- Containment operator skeleton: `containment/operator.go`
