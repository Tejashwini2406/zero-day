#!/usr/bin/env bash
set -euo pipefail

# Helper to gather datasets into data/
# Edit the placeholder commands (API keys, kaggle IDs, S3 paths) before running.

mkdir -p training/datasets

echo "This script contains placeholder commands for downloading datasets. Edit and run the ones you need."

echo "-- Kubernetes Anomaly Detection (Kaggle) --"
# Example: kaggle datasets download -d <owner/dataset-name> -p data/kubernetes_anomaly
echo "# kaggle datasets download -d <owner/dataset-name> -p training/datasets/kubernetes_anomaly"
echo "# Local sample (temporary) is available at training/datasets/samples/kubernetes_anomaly_events.jsonl"

echo "-- KubeiQ (S3 placeholder) --"
echo "# aws s3 cp s3://ppl-ai-file-upload/kubeiq/data.tar.gz training/datasets/kubeiq/ --recursive"
echo "# Local sample (temporary) is available at training/datasets/samples/kubeiq_events.jsonl"

echo "-- NSL-KDD --"
echo "# mkdir -p training/datasets/nslkdd && curl -o training/datasets/nslkdd/nsl-kdd.zip https://example.com/nslkdd.zip"
echo "# Local sample (temporary) is available at training/datasets/samples/nslkdd_sample.csv"

echo "-- OpenTelemetry eBPF Traces (GitHub) --"
echo "# git clone https://github.com/open-telemetry/opentelemetry-ebpf.git training/datasets/opentelemetry_ebpf"
echo "# Local sample (temporary) is available at training/datasets/samples/opentelemetry_syscalls.jsonl"

echo "-- Cloud Vulnerabilities (Kaggle) --"
echo "# kaggle datasets download -d <owner/cloud-vulns> -p training/datasets/cloud_vulns"
echo "# Local sample (temporary) is available at training/datasets/samples/cloud_vulns_sample.csv"

echo "-- Graph Anomaly Datasets (GitHub/Awesome lists) --"
echo "# See DATASETS.md for links and examples"
echo "# Local sample (temporary) is available at training/datasets/samples/graph_anomaly_events.jsonl"

echo "Done. Edit this script with real dataset IDs/URLs before running the commands above."
