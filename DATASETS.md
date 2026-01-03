# Datasets for Zero-Day Training and Evaluation

This document lists recommended datasets, descriptions, and suggested uses for training and validating the Zero-Day detection models.

| Dataset | Description | Use Case | Link |
|---|---|---|---|
| CTU-13 (Botnet Traces) | PCAP captures of botnet/benign traffic from CTU (Stratosphere Research) | Map network flows to pod-like flows; train baselines / TGNN | https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet/ |
| KubeiQ (S3 dataset) | Original S3 dataset not accessible without credentials; replaced by CTU-13 or local K8s audit logs for training | Production-like telemetry for graph construction | Use CTU-13 or collect cluster telemetry |
| NSL-KDD (Adapted) | Network intrusion dataset (map to pod flows) | Baseline validation, augment synthetic attacks | KDD Cup / NSL-KDD: https://www.unb.ca/cic/datasets/nsl.html |
| OpenTelemetry eBPF Traces | Kernel/container traces captured via eBPF | Use as syscall-level telemetry for synthetic generator | GitHub: https://github.com/open-telemetry/opentelemetry-ebpf |
| ExploitDB (vulnerabilities) | Public repository of exploits and vulnerability metadata (ExploitDB) | Use as vulnerability/POC examples to simulate cloud vulns in generator | https://github.com/offensive-security/exploitdb |
| Graph Anomaly Datasets | Temporal graph datasets (fraud, traffic) | TGNN pre-training / transfer learning | Awesome lists / GitHub (search "graph anomaly datasets") |

- Notes and suggestions
- Store datasets under `training/datasets/` (eg. `training/datasets/kubeiq/`, `training/datasets/nslkdd/`).
- Use the `scripts/download_datasets.sh` helper to gather data (some entries are placeholders requiring credentials/API keys). The helper now targets `training/datasets/`.
- For large datasets prefer running training in cloud or on a machine with sufficient disk/CPU/GPU.
- When adapting non-K8s datasets (e.g., NSL-KDD), map network flow fields to pod identifiers and temporal windows used by the graph builder.

Minimal workflow
1. Download dataset to `training/datasets/<dataset>/`.
2. Run `python -m graph_builder.main file --input-file training/datasets/<dataset>/events.jsonl --out-dir ./graphs` to build Parquet windows.
3. Run `python ml/train_datasets.py --data-dir ./graphs --out-dir ml_artifacts --model isolation` to run a small baseline.

If you want, I can try to download a small dataset and run the baseline locally—tell me which dataset to fetch first.
