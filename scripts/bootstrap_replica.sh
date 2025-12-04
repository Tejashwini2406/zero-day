#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script: start minikube, deploy Redpanda, build/load images and apply manifests
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

NAMESPACE_KAFKA=kafka
NAMESPACE_ML=ml

echo "Ensure namespaces exist"
kubectl create ns ${NAMESPACE_KAFKA} || true
kubectl create ns ${NAMESPACE_ML} || true

echo "Start minikube (if not running)"
minikube status >/dev/null 2>&1 || minikube start --driver=docker --memory=4096 --cpus=2

echo "Deploy Redpanda"
echo "Check for existing Kafka bootstrap service (Strimzi)"
if kubectl -n ${NAMESPACE_KAFKA} get svc my-cluster-kafka-bootstrap >/dev/null 2>&1; then
  echo "Found existing Strimzi Kafka bootstrap service; skipping Redpanda deploy"
  KAFKA_BOOTSTRAP="my-cluster-kafka-bootstrap.${NAMESPACE_KAFKA}:9092"
else
  if [ -f "infra/k8s/redpanda/redpanda-deployment.yaml" ]; then
    echo "Deploy Redpanda"
    kubectl -n ${NAMESPACE_KAFKA} apply -f infra/k8s/redpanda/redpanda-deployment.yaml
    echo "Wait for redpanda to be ready"
    kubectl -n ${NAMESPACE_KAFKA} wait --for=condition=available --timeout=120s deployment/redpanda || true
    KAFKA_BOOTSTRAP="redpanda.${NAMESPACE_KAFKA}:9092"
  else
    echo "No Strimzi bootstrap service and no Redpanda manifest found."
    echo "Please provide a Kafka bootstrap endpoint or add infra/k8s/redpanda/redpanda-deployment.yaml"
    exit 1
  fi
fi

echo "Build and load graph-builder image"
if docker build -t graph-builder:v7 graph_builder/; then
  minikube image load graph-builder:v7
fi

echo "Apply storage and app manifests"
kubectl apply -f infra/k8s/storage/pv-pvc-graphs.yaml || true
kubectl -n ${NAMESPACE_ML} apply -f infra/k8s/graph-builder/deployment.yaml || true
kubectl -n ${NAMESPACE_ML} apply -f infra/k8s/inference/configmap-inference-script.yaml || true
kubectl -n ${NAMESPACE_ML} apply -f infra/k8s/inference/deployment.yaml || true

echo "Create topic security-events (replication=1)"
kubectl -n ${NAMESPACE_KAFKA} run k-producer --rm -i --image=python:3.11-slim --env KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP}" -- bash -c "pip install kafka-python -q && python - <<'PY'
import os
bootstrap = os.environ.get('KAFKA_BOOTSTRAP', 'localhost:9092')
from kafka.admin import KafkaAdminClient, NewTopic
admin = KafkaAdminClient(bootstrap_servers=bootstrap)
try:
  admin.create_topics([NewTopic('security-events', num_partitions=1, replication_factor=1)])
except Exception as e:
  print('create topic:', e)
print('done')
PY"

echo "Bootstrap complete"
