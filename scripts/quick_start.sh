#!/usr/bin/env bash
set -euo pipefail

# Quick-start automation: builds images, deploys to Minikube, runs smoke tests.
# Usage: bash scripts/quick_start.sh

echo "=== Zero-Day Detection Framework Quick-Start ==="

# 1. Check minikube is running
echo "Checking Minikube..."
if ! minikube status | grep -q "Running"; then
  echo "Starting Minikube..."
  minikube start --driver=docker --nodes=3 --memory=8192 --cpus=4
fi

# 2. Setup base infra
echo "Setting up base infra..."
make apply-manifests

# 3. Setup telemetry (Kafka)
echo "Setting up telemetry..."
make setup-telemetry

# 4. Build images
echo "Building container images..."
make build-images

# 5. Load images into minikube
echo "Loading images into Minikube..."
minikube image load graph-builder:latest
minikube image load ml:latest
minikube image load inference:latest
minikube image load containment-operator:latest

# 6. Deploy services
echo "Deploying services..."
make deploy-all

# 7. Run smoke tests
echo "Running smoke tests..."
bash scripts/smoke_test.sh

echo "=== Quick-start complete ==="
echo "Next: check kubectl get pods -A to see all running services"
echo "See INTEGRATION_GUIDE.md for detailed testing and operational steps"
