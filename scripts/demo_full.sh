#!/usr/bin/env bash
set -euo pipefail

# Demo script: generate attack, ingest via graph-builder file mode,
# wait for inference, run lightweight XAI and copy explanation back.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Use the project's configured Python virtualenv so required packages are available
PYTHON_EXEC="/home/wini/zero-day/.venv/bin/python"

if [[ ! -x "$PYTHON_EXEC" ]]; then
  echo "Warning: venv python not found at $PYTHON_EXEC — falling back to system python3"
  PYTHON_EXEC=python3
fi

echo "1/6: Generating synthetic attack events"
${PYTHON_EXEC} scripts/generate_attack.py --out /tmp/attack_events.jsonl --count 800 --attack-start 120 --attack-burst 160 --benign-ratio 0.8

echo "2/6: Locating graph-builder and inference pods (namespace=ml)"
GB_POD=$(kubectl -n ml get pods -o name | grep graph-builder | head -n1 | cut -d/ -f2 || true)
INF_POD=$(kubectl -n ml get pods -o name | grep inference-watcher | head -n1 | cut -d/ -f2 || true)

if [[ -z "$GB_POD" || -z "$INF_POD" ]]; then
  echo "Could not find required pods in namespace 'ml'. Ensure manifests are applied and pods are running."
  kubectl -n ml get pods
  exit 2
fi

echo "Found graph-builder pod: $GB_POD"
echo "Found inference pod: $INF_POD"

echo "3/6: Copying attack events into graph-builder pod"
kubectl -n ml cp /tmp/attack_events.jsonl ${GB_POD}:/tmp/attack_events.jsonl

echo "4/6: Running graph-builder in file mode inside the pod"
kubectl -n ml exec -it ${GB_POD} -- python -m graph_builder.main file --input-file /tmp/attack_events.jsonl --out-dir /data/graphs

echo "5/6: Waiting for inference to process windows (10s)"
sleep 10

echo "Processed alert files in inference pod:"
kubectl -n ml exec ${INF_POD} -- bash -lc "ls -1 /data/processed || true"

echo "6/6: Run XAI on the latest nodes parquet and copy explanation back"
LATEST_NODES=$(kubectl -n ml exec ${GB_POD} -- bash -lc "ls -t /data/graphs/*nodes.parquet 2>/dev/null | head -n1" | tr -d '\r')
if [[ -z "$LATEST_NODES" ]]; then
  echo "No nodes parquet found under /data/graphs in graph-builder pod"
  exit 0
fi

echo "Latest nodes parquet: $LATEST_NODES"

kubectl -n ml cp ${GB_POD}:"${LATEST_NODES}" ./latest_nodes.parquet

echo "Running lightweight XAI explainer locally (using $PYTHON_EXEC)"
${PYTHON_EXEC} ml/xai_explain.py latest_nodes.parquet --out latest_nodes.parquet.xai.json --top-k 5

echo "Copying XAI explanation to inference pod /data/processed"
kubectl -n ml cp latest_nodes.parquet.xai.json ${INF_POD}:/data/processed/

echo "Done. Alerts and XAI files in inference pod:/data/processed"
kubectl -n ml exec ${INF_POD} -- bash -lc "ls -l /data/processed || true"

echo "Show the XAI JSON (local copy):"
cat latest_nodes.parquet.xai.json || true

echo "Demo finished. To follow live inference logs: kubectl -n ml logs -f $INF_POD"
