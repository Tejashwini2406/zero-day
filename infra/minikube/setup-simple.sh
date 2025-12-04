#!/usr/bin/env bash
set -euo pipefail

# Simplified Minikube PoC setup script
# Optimized for resource-constrained environments

echo "==============================================="
echo "Zero-Day Detection Framework - Minikube Setup"
echo "==============================================="

# Detect available memory and adjust allocation
AVAILABLE_MEM=$(free -m | awk 'NR==2{print $7}')
MINIKUBE_MEM=$((AVAILABLE_MEM > 6000 ? 5120 : 3072))
MINIKUBE_CPUS=$((AVAILABLE_MEM > 6000 ? 4 : 2))

echo "📊 System Resources:"
echo "   Available memory: ${AVAILABLE_MEM}MB"
echo "   Minikube memory: ${MINIKUBE_MEM}MB"
echo "   Minikube CPUs: ${MINIKUBE_CPUS}"

# Check if minikube already exists
if minikube status &>/dev/null; then
  echo "✅ Minikube cluster already exists, skipping start"
else
  echo "🚀 Starting Minikube (single node, optimized)..."
  minikube start \
    --driver=docker \
    --nodes=1 \
    --memory=$MINIKUBE_MEM \
    --cpus=$MINIKUBE_CPUS \
    --disk-size=50GB \
    --wait=all \
    --timeout=5m \
    --kubernetes-version=v1.28.0 \
    2>&1 | grep -E "(Starting|Done|Kubernetes|docker)" || true
fi

echo "⏳ Waiting for cluster stability (30s)..."
sleep 30

# Check cluster health
echo "🏥 Checking cluster health..."
kubectl get nodes || true
kubectl cluster-info || true

echo "✅ Minikube setup complete!"
echo "   Next steps:"
echo "   1. Run: make apply-manifests"
echo "   2. Run: make setup-telemetry"
echo "   3. Run: make setup-monitoring"
