#!/usr/bin/env bash
set -euo pipefail

echo "Checking Kafka operator pods in namespace kafka..."
kubectl -n kafka get pods

echo "Checking Kafka cluster resources..."
kubectl -n kafka get kafka

echo "Checking OpenTelemetry collector in monitoring namespace..."
kubectl -n monitoring get pods -l app=otel-collector

echo "Checking Fluent Bit DaemonSet..."
kubectl -n monitoring get ds fluent-bit

echo "Deploying sample app in dev namespace..."
kubectl apply -f ../infra/k8s/sample-app/sample-app.yaml

echo "Waiting 10s for sample logs to appear via Fluent Bit -> Kafka (give some time for Strimzi to become ready)"
sleep 10

echo "Smoke test completed: confirm by checking Kafka topics / consumer or view logs from Fluent Bit and OTel Collector pods."
