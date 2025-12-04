#!/usr/bin/env bash
set -euo pipefail

# Apply storage and inference manifests, then show demo steps
kubectl apply -f infra/k8s/storage/pv-pvc-graphs.yaml
kubectl apply -f infra/k8s/inference/configmap-inference-script.yaml
kubectl apply -f infra/k8s/inference/deployment.yaml

echo "Waiting for inference pod..."
kubectl -n ml wait --for=condition=available deployment/inference-watcher --timeout=120s || true

# Show current graph files
echo "Current /data/graphs files (from graph-builder pod):"
GB_POD=$(kubectl get pod -n ml -l app=graph-builder -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n ml "$GB_POD" -- ls -la /data/graphs || true

# Tail inference logs for 30 seconds
INF_POD=$(kubectl get pod -n ml -l app=inference-watcher -o jsonpath='{.items[0].metadata.name}')

echo "Tailing inference logs (30s):"
kubectl logs -n ml -f "$INF_POD" &
LOG_PID=$!
sleep 30
kill $LOG_PID || true

echo "Processed alerts (on PVC):"
kubectl exec -n ml "$GB_POD" -- ls -la /data/processed || true

