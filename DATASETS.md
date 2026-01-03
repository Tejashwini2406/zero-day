# Datasets for Zero-Day Training and Evaluation

This document lists recommended datasets, descriptions, and suggested uses for training and validating the Zero-Day detection models.

| Dataset | Description | Use Case | Link |
|---|---|---|---|
| Kubernetes Anomaly Detection Dataset | Pod metrics, logs, network flows for container anomalies | Direct replacement for synthetic; train baselines / TGNN | Kaggle: https://www.kaggle.com/ (search "Kubernetes Anomaly Detection Dataset") |
| KubeiQ (Dataset) | Auto-generated Kubernetes anomalies across clusters | Production-like telemetry for graph construction | S3 placeholder: ppl-ai-file-upload.s3.amazonaws.com/kubeiq |
| NSL-KDD (Adapted) | Network intrusion dataset (map to pod flows) | Baseline validation, augment synthetic attacks | KDD Cup / NSL-KDD: https://www.unb.ca/cic/datasets/nsl.html |
| OpenTelemetry eBPF Traces | Kernel/container traces captured via eBPF | Use as syscall-level telemetry for synthetic generator | GitHub: https://github.com/open-telemetry/opentelemetry-ebpf |
| Cloud Vulnerabilities | Collection of cloud vulnerabilities (AWS/GCP/Azure) | Simulate zero-days in synthetic generator | Kaggle: https://www.kaggle.com/ (search "cloud vulnerabilities") |
| Graph Anomaly Datasets | Temporal graph datasets (fraud, traffic) | TGNN pre-training / transfer learning | Awesome lists / GitHub (search "graph anomaly datasets") |

- Notes and suggestions
- Store datasets under `training/datasets/` (eg. `training/datasets/kubeiq/`, `training/datasets/nslkdd/`).
- Use the `scripts/download_datasets.sh` helper to gather data (some entries are placeholders requiring credentials/API keys). The helper now targets `training/datasets/`.
- For large datasets prefer running training in cloud or on a machine with sufficient disk/CPU/GPU.
- When adapting non-K8s datasets (e.g., NSL-KDD), map network flow fields to pod identifiers and temporal windows used by the graph builder.

Minimal workflow
1. Download dataset to `data/<dataset>/`.
2. Run `python -m graph_builder.main file --input-file data/<dataset>/events.jsonl --out-dir ./graphs` to build Parquet windows.
3. Run `python ml/train_datasets.py --data-dir ./graphs --out-dir ml_artifacts --model isolation` to run a small baseline.

If you want, I can try to download a small dataset and run the baseline locally—tell me which dataset to fetch first.
