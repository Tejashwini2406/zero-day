#!/usr/bin/env bash
set -euo pipefail

# Minimal Minikube + Istio + Cilium PoC setup script
# Run this on a Linux host with Docker available. Adjust resources as needed.

echo "Starting Minikube (2 nodes, adjusted resources)..."
# Detect available memory and adjust allocation
AVAILABLE_MEM=$(free -m | awk 'NR==2{print $7}')
MINIKUBE_MEM=$((AVAILABLE_MEM > 6000 ? 6144 : 3072))
echo "Detected available memory: ${AVAILABLE_MEM}MB. Allocating: ${MINIKUBE_MEM}MB to Minikube"
minikube start --driver=docker --nodes=2 --memory=$MINIKUBE_MEM --cpus=4 --disk-size=50GB

echo "Installing Istio (demo profile)..."
if ! command -v istioctl &>/dev/null; then
  echo "istioctl not found. Please install Istio CLI first: https://istio.io/latest/docs/setup/getting-started/#download"
  exit 1
fi
istioctl install --set profile=demo -y

echo "Labeling default namespace for sidecar injection"
kubectl label namespace default istio-injection=enabled --overwrite || true

echo "Installing Cilium via Helm"
helm repo add cilium https://helm.cilium.io/ || true
helm repo update
kubectl create namespace cilium || true
helm upgrade --install cilium cilium/cilium --namespace kube-system \
  --set global.nodeinit.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true

echo "Creating baseline namespaces and applying manifests"
kubectl apply -f ../k8s/namespaces.yaml
kubectl apply -f ../k8s/networkpolicies.yaml
kubectl apply -f ../k8s/rbac.yaml

echo "Minikube + Istio + Cilium setup completed."
echo "Next: deploy telemetry collectors and the remainder of the pipeline (see README)."
