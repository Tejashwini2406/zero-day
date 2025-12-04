#!/usr/bin/env bash
set -euo pipefail

echo "Installing Strimzi via Helm (chart)"
helm repo add strimzi https://strimzi.io/charts || true
helm repo update

kubectl create namespace kafka || true

helm upgrade --install strimzi-kafka strimzi/strimzi-kafka-operator --namespace kafka

echo "Applying Kafka Cluster custom resource (single-node broker for PoC)"
kubectl apply -f ../k8s/kafka/kafka-cluster.yaml

echo "Waiting for Kafka pods to be ready..."
kubectl -n kafka wait --for=condition=Ready pod -l strimzi.io/name=my-cluster-kafka-0 --timeout=300s || true

echo "Strimzi + Kafka installed."
