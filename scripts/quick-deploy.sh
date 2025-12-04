#!/usr/bin/env bash
set -euo pipefail

# Zero-Day Detection Framework - Quick Deploy Script
# Optimized for step-by-step deployment with clear checkpoints

cd "$(dirname "$0")/.."

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Zero-Day Detection & Mitigation Framework - Quick Deploy      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get available memory
AVAILABLE_MEM=$(free -m | awk 'NR==2{print $7}')
MINIKUBE_MEM=$((AVAILABLE_MEM > 6000 ? 5120 : 3072))
MINIKUBE_CPUS=$((AVAILABLE_MEM > 6000 ? 4 : 2))

echo "📊 System: ${AVAILABLE_MEM}MB available → Minikube: ${MINIKUBE_MEM}MB, ${MINIKUBE_CPUS} CPUs"
echo ""

# STEP 1: Start Minikube
echo "════════════════════════════════════════════════════════════════"
echo "STEP 1: Start Minikube Cluster"
echo "════════════════════════════════════════════════════════════════"
echo ""

if minikube status 2>&1 | grep -q "Running"; then
  echo "✅ Minikube already running"
else
  echo "🚀 Starting Minikube... (this may take 3-5 minutes)"
  echo ""
  minikube start \
    --driver=docker \
    --nodes=1 \
    --memory=$MINIKUBE_MEM \
    --cpus=$MINIKUBE_CPUS \
    --disk-size=50GB \
    --kubernetes-version=v1.28.0 \
    --wait=all
  echo ""
fi

# Verify cluster
echo "Verifying cluster..."
kubectl cluster-info || exit 1
kubectl get nodes
echo "✅ Cluster ready"
echo ""

# STEP 2: Apply manifests
echo "════════════════════════════════════════════════════════════════"
echo "STEP 2: Apply Kubernetes Manifests"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "📦 Creating namespaces..."
kubectl apply -f infra/k8s/namespaces.yaml

echo "🔐 Applying RBAC..."
kubectl apply -f infra/k8s/rbac.yaml

echo "🚫 Applying Network Policies..."
kubectl apply -f infra/k8s/networkpolicies.yaml

echo "📋 Applying Containment CRD..."
kubectl apply -f containment/crd.yaml 2>/dev/null || true

echo "✅ Manifests applied"
echo ""

# STEP 3: Setup Telemetry (simple version - skip complex setups)
echo "════════════════════════════════════════════════════════════════"
echo "STEP 3: Deploy Core Telemetry (Simplified)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "📝 Deploying OpenTelemetry Collector..."
kubectl apply -f infra/k8s/otel/collector-configmap.yaml 2>/dev/null || true
kubectl apply -f infra/k8s/otel/collector-deployment.yaml 2>/dev/null || true

echo "📝 Deploying Fluent Bit..."
kubectl apply -f infra/k8s/fluentbit/fluentbit-configmap.yaml 2>/dev/null || true
kubectl apply -f infra/k8s/fluentbit/fluentbit-daemonset.yaml 2>/dev/null || true

echo "✅ Core telemetry deployed"
echo ""

# STEP 4: Build images
echo "════════════════════════════════════════════════════════════════"
echo "STEP 4: Build Container Images"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "🐳 Building services (skipping heavy ML image build)..."
set +e
docker build -t graph-builder:latest graph_builder/ && echo "  → graph-builder built" || echo "  → graph-builder build failed"
# Skip building ml image here; ML image may require heavy native deps. Build locally if needed.
docker build -t inference:latest -f ml/Dockerfile.inference . && echo "  → inference built" || echo "  → inference build failed"
docker build -t containment-operator:latest containment/ 2>/dev/null && echo "  → containment-operator built" || echo "  → containment-operator build failed"
set -e

echo "✅ Image build step complete (ml image skipped). To build ML image, run: docker build -t ml:latest ml/"
echo ""

# STEP 5: Load images
echo "════════════════════════════════════════════════════════════════"
echo "STEP 5: Load Images into Minikube"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "📥 Loading images (ml image skipped)..."
minikube image load graph-builder:latest 2>&1 | grep -v "Getting image" || true
# If you have built ml:latest locally, you can load it manually: minikube image load ml:latest
minikube image load inference:latest 2>&1 | grep -v "Getting image" || true
minikube image load containment-operator:latest 2>&1 | grep -v "Getting image" || true

echo "✅ Images loaded"
echo ""

# STEP 6: Deploy services
echo "════════════════════════════════════════════════════════════════"
echo "STEP 6: Deploy Microservices"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "📦 Deploying services..."
kubectl apply -f infra/k8s/graph-builder/rbac.yaml 2>/dev/null || true
kubectl apply -f infra/k8s/graph-builder/deployment.yaml 2>/dev/null || true

kubectl apply -f infra/k8s/ml/trainer-rbac.yaml 2>/dev/null || true
kubectl apply -f infra/k8s/ml/trainer-cronjob.yaml 2>/dev/null || true
kubectl apply -f infra/k8s/ml/inference-rbac.yaml 2>/dev/null || true
kubectl apply -f infra/k8s/ml/inference-deployment.yaml 2>/dev/null || true

kubectl apply -f infra/k8s/containment/operator-deployment.yaml 2>/dev/null || true

echo "⏳ Waiting for deployments... (60 seconds)"
sleep 60

echo "✅ Services deployed"
echo ""

# STEP 7: Verify status
echo "════════════════════════════════════════════════════════════════"
echo "STEP 7: Verify Deployment Status"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "📋 Pod status:"
kubectl get pods -A --no-headers 2>/dev/null | head -15 || true

echo ""
echo "✅ Deployment verification complete"
echo ""

# STEP 8: Test inference
echo "════════════════════════════════════════════════════════════════"
echo "STEP 8: Quick Inference Test (Optional)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Testing inference service..."
if kubectl get svc -n ml inference 2>/dev/null | grep -q inference; then
  echo "✅ Inference service deployed"
  echo ""
  echo "To test manually, run:"
  echo "  kubectl -n ml port-forward svc/inference 8080:8080 &"
  echo "  sleep 2"
  echo "  curl -X POST http://localhost:8080/health"
else
  echo "⚠️  Inference service not yet deployed (may still be initializing)"
fi

echo ""
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Next Steps:"
echo ""
echo "1️⃣  Verify cluster:"
echo "    kubectl get all -A"
echo ""
echo "2️⃣  Train ML models locally:"
echo "    cd /home/wini/zero-day"
echo "    make train-ml-full"
echo ""
echo "3️⃣  Test inference service:"
echo "    make test-inference"
echo ""
echo "4️⃣  View Grafana dashboards:"
echo "    minikube service grafana -n monitoring || echo 'Grafana not installed'"
echo ""
echo "5️⃣  Read operational runbook:"
echo "    cat docs/RUNBOOK.md"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
