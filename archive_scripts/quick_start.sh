#!/usr/bin/env bash
set -euo pipefail

# Quick-start automation: builds images, deploys to Minikube, runs smoke tests.
# Usage: bash scripts/quick_start.sh

echo "=== Zero-Day Detection Framework Quick-Start ==="

echo "Checking Minikube..."
if ! minikube status | grep -q "Running"; then
  echo "Starting Minikube..."
  minikube start --driver=docker --nodes=3 --memory=8192 --cpus=4
fi

echo "Setting up base infra..."
make apply-manifests

echo "Setting up telemetry..."
make setup-telemetry

echo "Building container images..."
make build-images

echo "Loading images into Minikube..."
minikube image load graph-builder:latest
minikube image load ml:latest
minikube image load inference:latest
minikube image load containment-operator:latest

echo "Deploying services..."
make deploy-all

echo "Running smoke tests..."
bash scripts/smoke_test.sh

echo "=== Quick-start complete ==="
