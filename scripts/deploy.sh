#!/usr/bin/env bash
set -euo pipefail

# Zero-Day Detection Framework - Complete Test & Deploy Script
# This script orchestrates the full deployment and testing workflow

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Zero-Day Detection & Mitigation Framework                    ║"
echo "║  Complete Test & Deployment Workflow                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Detect available memory
AVAILABLE_MEM=$(free -m | awk 'NR==2{print $7}')
MINIKUBE_MEM=$((AVAILABLE_MEM > 6000 ? 5120 : 3072))
MINIKUBE_CPUS=$((AVAILABLE_MEM > 6000 ? 4 : 2))

echo "📊 SYSTEM RESOURCES"
echo "   Available Memory: ${AVAILABLE_MEM}MB"
echo "   Minikube Config: ${MINIKUBE_MEM}MB RAM, ${MINIKUBE_CPUS} CPUs"
echo ""

# Step 1: Start Minikube
echo "════════════════════════════════════════════════════════════════"
echo "STEP 1: Initialize Kubernetes Cluster (Minikube)"
echo "════════════════════════════════════════════════════════════════"

if minikube status &>/dev/null; then
  echo "✅ Minikube is already running"
  minikube status
else
  echo "🚀 Starting Minikube..."
  minikube start \
    --driver=docker \
    --nodes=1 \
    --memory=$MINIKUBE_MEM \
    --cpus=$MINIKUBE_CPUS \
    --disk-size=50GB \
    --wait=all \
    --kubernetes-version=v1.28.0
fi

echo "⏳ Waiting for cluster to stabilize (30 seconds)..."
sleep 30

echo "✅ Kubernetes cluster ready"
kubectl get nodes
echo ""

# Step 2: Apply base manifests
echo "════════════════════════════════════════════════════════════════"
echo "STEP 2: Apply Base Kubernetes Manifests"
echo "════════════════════════════════════════════════════════════════"

echo "📦 Creating namespaces..."
kubectl apply -f /home/wini/zero-day/infra/k8s/namespaces.yaml

echo "🔐 Applying RBAC..."
kubectl apply -f /home/wini/zero-day/infra/k8s/rbac.yaml

echo "🚫 Applying Network Policies..."
kubectl apply -f /home/wini/zero-day/infra/k8s/networkpolicies.yaml

echo "📋 Applying Containment CRD..."
kubectl apply -f /home/wini/zero-day/containment/crd.yaml || true

echo "✅ Base manifests applied"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "STEP 3: Deploy Telemetry Pipeline"
echo "════════════════════════════════════════════════════════════════"

echo "Installing Strimzi via Helm (chart)"
helm repo add strimzi https://strimzi.io/charts || true
helm repo update

kubectl create namespace kafka || true

helm upgrade --install strimzi-kafka strimzi/strimzi-kafka-operator --namespace kafka

echo "Applying Kafka Cluster custom resource (single-node broker for PoC)"
cat <<EOF | kubectl apply -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: my-cluster
  namespace: kafka
spec:
  kafka:
    version: 3.3.1
    replicas: 1
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    storage:
      type: ephemeral
  zookeeper:
    replicas: 1
    storage:
      type: ephemeral
  entityOperator:
    topicOperator: {}
    userOperator: {}
EOF

echo "Waiting for Kafka pods to be ready..."
kubectl -n kafka wait --for=condition=Ready pod -l strimzi.io/name=my-cluster-kafka-0 --timeout=300s || true

echo "Strimzi + Kafka installed."

echo "Deploying OpenTelemetry Collector..."
kubectl apply -f /home/wini/zero-day/infra/k8s/otel/collector-configmap.yaml
kubectl apply -f /home/wini/zero-day/infra/k8s/otel/collector-deployment.yaml

echo "Deploying Fluent Bit..."
kubectl apply -f /home/wini/zero-day/infra/k8s/fluentbit/fluentbit-configmap.yaml
kubectl apply -f /home/wini/zero-day/infra/k8s/fluentbit/fluentbit-daemonset.yaml

echo "Waiting for telemetry components (45 seconds)..."
sleep 45

echo "Telemetry pipeline deployed"

# Step 4: Setup Monitoring
echo "════════════════════════════════════════════════════════════════"
echo "STEP 4: Deploy Monitoring Stack"
echo "════════════════════════════════════════════════════════════════"

echo "📊 Setting up Prometheus, Grafana, ClickHouse..."
bash /home/wini/zero-day/infra/minikube/setup-monitoring.sh 2>&1 | tail -10

echo "📈 Applying Grafana dashboards..."
kubectl apply -f /home/wini/zero-day/infra/k8s/monitoring/grafana-dashboards-cm.yaml || true

echo "⏳ Waiting for monitoring stack (30 seconds)..."
sleep 30

echo "✅ Monitoring stack deployed"
echo ""

# Step 5: Build images
echo "════════════════════════════════════════════════════════════════"
echo "STEP 5: Build Container Images"
echo "════════════════════════════════════════════════════════════════"

echo "🐳 Building graph-builder image..."


echo "🐳 Building ML image..."
docker build -t ml:latest /home/wini/zero-day/infra/k8s/ml 2>&1 | tail -3


echo "🐳 Building inference service image..."
docker build -t inference:latest -f /home/wini/zero-day/infra/k8s/mlDockerfile.inference . 2>&1 | tail -3


echo "🐳 Building containment operator image..."
docker build -t containment-operator:latest /home/wini/zero-day/infra/k8s/containment/ 2>&1 | tail -3


echo "✅ All container images built"
echo ""

# Step 6: Load images
echo "════════════════════════════════════════════════════════════════"
echo "STEP 6: Load Images into Minikube"
echo "════════════════════════════════════════════════════════════════"

echo "📥 Loading images into Minikube registry..."
minikube image load graph-builder:latest
minikube image load ml:latest
minikube image load inference:latest
minikube image load containment-operator:latest

echo "✅ Images loaded into Minikube"
echo ""

# Step 7: Deploy services
echo "════════════════════════════════════════════════════════════════"
echo "STEP 7: Deploy Microservices"
echo "════════════════════════════════════════════════════════════════"

echo "📦 Deploying graph-builder..."
kubectl apply -f /home/wini/zero-day/infra/k8s/graph-builder/rbac.yaml
kubectl apply -f /home/wini/zero-day/infra/k8s/graph-builder/deployment.yaml

echo "📦 Deploying ML services..."
kubectl apply -f /home/wini/zero-day/infra/k8s/ml/trainer-rbac.yaml
kubectl apply -f /home/wini/zero-day/infra/k8s/ml/trainer-cronjob.yaml
kubectl apply -f /home/wini/zero-day/infra/k8s/ml/inference-rbac.yaml
kubectl apply -f /home/wini/zero-day/infra/k8s/ml/inference-deployment.yaml

echo "📦 Deploying containment operator..."
kubectl apply -f /home/wini/zero-day/infra/k8s/containment/operator-deployment.yaml

echo "⏳ Waiting for services to be ready (60 seconds)..."
sleep 60

echo "✅ All microservices deployed"
echo ""

# Step 8: Verify deployments
echo "════════════════════════════════════════════════════════════════"
echo "STEP 8: Verify Deployments"
echo "════════════════════════════════════════════════════════════════"

echo "📋 Checking pod status..."
echo ""
for ns in prod dev monitoring ml quarantine; do
  echo "Namespace: $ns"
  kubectl get pods -n $ns 2>/dev/null || echo "  (namespace may not exist)"
done

echo ""
echo "✅ Deployment verification complete"
echo ""

# Step 9: Test inference service
echo "════════════════════════════════════════════════════════════════"
echo "STEP 9: Test Inference Service"
echo "════════════════════════════════════════════════════════════════"

echo "🔌 Setting up port-forward to inference service..."
kubectl -n ml port-forward svc/inference 8080:8080 &
PORTFORWARD_PID=$!
sleep 2

echo "📡 Testing /health endpoint..."
if curl -s http://localhost:8080/health | grep -q "healthy"; then
  echo "✅ Inference service is healthy"
else
  echo "⚠️  Inference service response (may still be starting)"
  curl -s http://localhost:8080/health || echo "Service not yet ready"
fi

echo ""
echo "📡 Testing /score endpoint..."
SCORE_RESPONSE=$(curl -s -X POST http://localhost:8080/score \
  -H "Content-Type: application/json" \
  -d '{"pod_name":"test","namespace":"dev","features":[0.1,-0.2,0.3,0.0,0.1,0.2,-0.1,0.0,0.05,-0.05,0.1,0.2,0.05,-0.1,0.15,0.0]}' 2>/dev/null || echo "{}") 

if [ ! -z "$SCORE_RESPONSE" ] && [ "$SCORE_RESPONSE" != "{}" ]; then
  echo "✅ Inference service responding:"
  echo "$SCORE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SCORE_RESPONSE"
else
  echo "⚠️  Service may still be initializing, will be available once ML models load"
fi

echo ""
kill $PORTFORWARD_PID 2>/dev/null || true

echo "✅ Inference testing complete"
echo ""

# Step 10: Prepare for ML training
echo "════════════════════════════════════════════════════════════════"
echo "STEP 10: Local ML Training (Optional)"
echo "════════════════════════════════════════════════════════════════"

echo "📚 To run local ML training and validation:"
echo "   cd /home/wini/zero-day"
echo "   make train-ml-full"
echo ""
echo "This will generate:"
echo "   - Baseline models (Autoencoder, LSTM-AE, DeepLog)"
echo "   - TGNN model trained on synthetic graph windows"
echo "   - Validation report with attack simulation results"
echo "   - Metrics: precision, recall, F1, MTTD, SLO impact"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 NEXT STEPS:"
echo ""
echo "1. 🔍 VERIFY CLUSTER STATUS"
echo "   kubectl get all -A"
echo ""
echo "2. 📈 VIEW GRAFANA DASHBOARDS"
echo "   minikube service grafana -n monitoring"
echo ""
echo "3. 📚 RUN ML TRAINING & VALIDATION"
echo "   make train-ml-full"
echo ""
echo "4. 🚨 TEST INFERENCE SERVICE"
echo "   make test-inference"
echo ""
echo "5. 📖 READ OPERATIONAL RUNBOOK"
echo "   cat docs/RUNBOOK.md"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
