SHELL := /usr/bin/env bash

.PHONY: setup-minikube apply-manifests teardown setup-telemetry setup-monitoring setup-audit train-ml train-ml-full build-images deploy-graph-builder deploy-ml deploy-operator deploy-all test-inference validate-all

setup-minikube:
	@echo "Starting local Minikube PoC..."
	bash infra/minikube/setup.sh

setup-telemetry:
	@echo "Installing telemetry components: Strimzi Kafka, OTel Collector, Fluent Bit"
	bash infra/minikube/setup-kafka.sh
	kubectl apply -f infra/k8s/otel/collector-configmap.yaml
	kubectl apply -f infra/k8s/otel/collector-deployment.yaml
	kubectl apply -f infra/k8s/fluentbit/fluentbit-configmap.yaml
	kubectl apply -f infra/k8s/fluentbit/fluentbit-daemonset.yaml

setup-monitoring:
	@echo "Installing monitoring + storage stack (Prometheus/Grafana, ClickHouse)"
	bash infra/minikube/setup-monitoring.sh
	kubectl apply -f infra/k8s/monitoring/grafana-dashboards-cm.yaml || true

setup-audit:
	@echo "Apply Kubernetes audit policy (requires kube-apiserver config changes)"
	kubectl apply -f infra/k8s/audit-policy.yaml || true

train-ml:
	@echo "Run ML baseline training locally (requires python deps)"
	bash ml/run_train.sh

train-ml-full:
	@echo "Run comprehensive ML training (baselines + TGNN + validation)"
	bash ml/run_full_train.sh

apply-manifests:
	@echo "Applying K8s manifests (base)..."
	kubectl apply -f infra/k8s/namespaces.yaml
	kubectl apply -f infra/k8s/rbac.yaml
	kubectl apply -f infra/k8s/networkpolicies.yaml
	kubectl apply -f containment/crd.yaml

build-images:
	@echo "Building container images (requires docker/buildkit)"
	docker build -t graph-builder:latest graph_builder/
	docker build -t ml:latest ml/
	docker build -t inference:latest -f ml/Dockerfile.inference .
	docker build -t containment-operator:latest containment/
	docker build -t zero-day-ui:latest ui/

deploy-graph-builder:
	@echo "Deploy graph-builder into ml namespace"
	kubectl apply -f infra/k8s/graph-builder/rbac.yaml
	kubectl apply -f infra/k8s/graph-builder/deployment.yaml

deploy-ml:
	@echo "Deploy ML training and inference services"
	kubectl apply -f infra/k8s/ml/trainer-rbac.yaml
	kubectl apply -f infra/k8s/ml/trainer-cronjob.yaml
	kubectl apply -f infra/k8s/ml/inference-rbac.yaml
	kubectl apply -f infra/k8s/ml/inference-deployment.yaml

deploy-operator:
	@echo "Deploy containment operator"
	kubectl apply -f infra/k8s/containment/operator-deployment.yaml

deploy-ui:
	@echo "Deploy UI dashboard"
	kubectl apply -f infra/k8s/ui/rbac.yaml
	kubectl apply -f infra/k8s/ui/deployment.yaml
	kubectl apply -f infra/k8s/ui/service.yaml

deploy-all: apply-manifests deploy-graph-builder deploy-ml deploy-operator deploy-ui
	@echo "All Kubernetes resources deployed"

test-inference:
	@echo "Test inference service (requires port-forward)"
	kubectl -n ml port-forward svc/inference 8080:8080 &
	sleep 2
	curl -X POST http://localhost:8080/score \
	  -H "Content-Type: application/json" \
	  -d '{"pod_name":"test","namespace":"dev","features":[0.1,-0.2,0.3,0.0,0.1,0.2,-0.1,0.0,0.05,-0.05,0.1,0.2,0.05,-0.1,0.15,0.0]}'
	pkill -f "port-forward" || true

validate-all: train-ml-full
	@echo "Complete validation suite (attacks, metrics, report)"
	@echo "See ml/ml_artifacts/validation_results.json for results"

teardown:
	@echo "Stopping minikube..."
	minikube stop || true
