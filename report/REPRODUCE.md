Reproducibility & Handoff
=========================

This document explains how to reproduce the PoC (Minikube, Kafka, graph-builder, inference, XAI) and where to find deliverables.

Prerequisites
- Linux or macOS with Docker and Minikube installed
- kubectl configured and able to talk to Minikube
- Recommended: at least 4GB RAM for Minikube

Quick bootstrap (recommended)
1. Start minikube (if not running):

```bash
minikube start --driver=docker --memory=4096 --cpus=2
```

2. Run the bootstrap script (creates namespaces, builds image, applies manifests, creates topic):

```bash
bash scripts/bootstrap_replica.sh
```

Notes:
- The bootstrap script prefers an existing Strimzi bootstrap service (`my-cluster-kafka-bootstrap`). If your cluster does not have Strimzi, add a working Redpanda manifest into `infra/k8s/redpanda/redpanda-deployment.yaml` before running the script.
- If the bootstrap aborts with a message about missing Kafka bootstrap, provide the bootstrap address via the environment:

```bash
KAFKA_BOOTSTRAP=your-kafka:9092 bash scripts/bootstrap_replica.sh
```

Run the demo (end-to-end)
1. Produce a scripted attack and run the file-mode demo (this will push events into the PVC and trigger inference & XAI):

```bash
bash scripts/demo_full.sh
```

2. Inspect inference outputs in the `inference` pod:

```bash
kubectl -n ml exec -it $(kubectl -n ml get pod -l app=inference-watcher -o jsonpath='{.items[0].metadata.name}') -- ls -la /data/processed
kubectl -n ml exec -it $(kubectl -n ml get pod -l app=inference-watcher -o jsonpath='{.items[0].metadata.name}') -- cat /data/processed/latest_nodes.parquet.xai.json
```

Deliverables
- DOCX reports are in `report/`.

Support notes
- If `graph-builder` doesn't consume historic messages, the consumer may be starting at `latest` offset. For deterministic demos, either restart the consumer before producing messages or set the consumer to `auto_offset_reset='earliest'` in `graph_builder/kafka_consumer.py`.
