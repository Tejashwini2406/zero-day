#!/usr/bin/env bash
set -euo pipefail

echo "Installing monitoring stack (Prometheus / Grafana) via kube-prometheus-stack (Helm)"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
helm repo add grafana https://grafana.github.io/helm-charts || true
helm repo update

kubectl create namespace monitoring || true

# Install kube-prometheus-stack
helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

echo "Installing ClickHouse (optional) via Helm (use clickhouse operator/chart)"
helm repo add clickhouse https://clickhouse.github.io/helm-charts || true
helm repo update
kubectl create namespace clickhouse || true
helm upgrade --install clickhouse clickhouse/clickhouse --namespace clickhouse || true

echo "Monitoring stack install complete. Access Grafana with port-forwarding or via minikube service if exposed."
echo "To port-forward Grafana: kubectl -n monitoring port-forward svc/kube-prometheus-grafana 3000:80"
