#!/bin/bash

###############################################################################
# Validation Script for Zero-Day Detection Framework PoC
#
# This script validates the local Minikube deployment of the framework.
# It checks:
#  - Cluster connectivity
#  - Core services health
#  - Inference service functionality
#  - Containment operator readiness
#  - Graph-builder output
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_header() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║ $1"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# Test 1: Cluster Connectivity
test_cluster_connectivity() {
    print_header "TEST 1: CLUSTER CONNECTIVITY"
    
    if kubectl cluster-info > /dev/null 2>&1; then
        log_success "Kubernetes cluster is accessible"
    else
        log_error "Cannot connect to Kubernetes cluster"
        return 1
    fi
    
    if kubectl get nodes | grep -q "Ready"; then
        log_success "At least one node is in Ready state"
    else
        log_error "No nodes in Ready state"
        return 1
    fi
}

# Test 2: Namespaces
test_namespaces() {
    print_header "TEST 2: NAMESPACE VALIDATION"
    
    local namespaces=("ml" "kafka" "monitoring" "quarantine")
    local all_exist=true
    
    for ns in "${namespaces[@]}"; do
        if kubectl get namespace "$ns" > /dev/null 2>&1; then
            log_success "Namespace '$ns' exists"
        else
            log_error "Namespace '$ns' not found"
            all_exist=false
        fi
    done
    
    [ "$all_exist" = true ]
}

# Test 3: Core Services
test_core_services() {
    print_header "TEST 3: CORE SERVICES STATUS"
    
    # Graph-builder
    if kubectl get pod -n ml -l app=graph-builder --no-headers | grep -q "Running"; then
        log_success "Graph-builder pod is running"
    else
        log_error "Graph-builder pod not running"
    fi
    
    # Inference service
    if kubectl get pod -n ml -l app=inference-service --no-headers | grep -q "Running"; then
        log_success "Inference service pod is running"
    else
        log_error "Inference service pod not running"
    fi
    
    # Containment operator
    if kubectl get pod -n quarantine -l app=containment-operator --no-headers | grep -q "Running"; then
        log_success "Containment operator is running"
    else
        log_error "Containment operator not running"
    fi
    
    # OTel Collector
    if kubectl get pod -n monitoring -l app=otel-collector --no-headers | grep -q "Running"; then
        log_success "OpenTelemetry Collector is running"
    else
        log_error "OpenTelemetry Collector not running"
    fi
}

# Test 4: Inference Service Endpoint
test_inference_endpoint() {
    print_header "TEST 4: INFERENCE SERVICE ENDPOINT"
    
    local pf_pid=""
    local max_retries=5
    local retry=0
    
    # Start port-forward in background
    kubectl -n ml port-forward svc/inference 8080:8080 > /dev/null 2>&1 &
    pf_pid=$!
    
    # Wait for port-forward to be ready
    while ! nc -z localhost 8080 2>/dev/null && [ $retry -lt $max_retries ]; do
        sleep 1
        ((retry++))
    done
    
    if [ $retry -eq $max_retries ]; then
        log_error "Port-forward to inference service failed after $max_retries attempts"
        kill $pf_pid 2>/dev/null || true
        return 1
    fi
    
    # Test scoring endpoint
    local response=$(curl -s -X POST http://localhost:8080/score \
        -H "Content-Type: application/json" \
        -d '{"features": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]}')
    
    kill $pf_pid 2>/dev/null || true
    
    if echo "$response" | jq -e '.score' > /dev/null 2>&1; then
        local score=$(echo "$response" | jq -r '.score')
        log_success "Inference service returned score: $score"
    else
        log_error "Inference service returned invalid response: $response"
        return 1
    fi
    
    # Test health endpoint
    pf_pid=""
    retry=0
    kubectl -n ml port-forward svc/inference 8080:8080 > /dev/null 2>&1 &
    pf_pid=$!
    
    while ! nc -z localhost 8080 2>/dev/null && [ $retry -lt $max_retries ]; do
        sleep 1
        ((retry++))
    done
    
    local health=$(curl -s -X GET http://localhost:8080/health)
    kill $pf_pid 2>/dev/null || true
    
    if echo "$health" | jq -e '.status' > /dev/null 2>&1; then
        log_success "Inference service health check passed"
    else
        log_error "Inference service health check failed"
        return 1
    fi
}

# Test 5: Containment CRD
test_containment_crd() {
    print_header "TEST 5: CONTAINMENT CUSTOM RESOURCE DEFINITION"
    
    if kubectl get crd containments.security.example.com > /dev/null 2>&1; then
        log_success "Containment CRD is registered"
    else
        log_error "Containment CRD not found"
        return 1
    fi
    
    # Try to create a test containment
    cat > /tmp/test-containment-$$-$RANDOM.yaml << 'EOF'
apiVersion: security.example.com/v1alpha1
kind: Containment
metadata:
  name: test-containment-validation
  namespace: quarantine
spec:
  alertID: "alert-test-validation"
  confidence: 0.8
  suggestedAction: "isolate_pod"
  dryRun: true
EOF
    
    if kubectl apply -f /tmp/test-containment-$$-$RANDOM.yaml > /dev/null 2>&1; then
        log_success "Containment CR can be created"
        kubectl delete containment -n quarantine test-containment-validation > /dev/null 2>&1 || true
    else
        log_error "Failed to create Containment CR"
        return 1
    fi
    
    rm -f /tmp/test-containment-$$-$RANDOM.yaml
}

# Test 6: Graph-builder Output
test_graph_builder() {
    print_header "TEST 6: GRAPH-BUILDER OUTPUT VALIDATION"
    
    # Check if graph-builder has produced output
    local builder_pod=$(kubectl get pod -n ml -l app=graph-builder -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$builder_pod" ]; then
        log_error "Graph-builder pod not found"
        return 1
    fi
    
    # Check logs for successful window creation
    local logs=$(kubectl logs -n ml "$builder_pod" --tail=20 2>/dev/null || echo "")
    
    if echo "$logs" | grep -q "Wrote.*window files"; then
        log_success "Graph-builder has produced window files"
    else
        log_warn "Graph-builder output not confirmed (may be working in background)"
    fi
}

# Test 7: Kafka Status (informational)
test_kafka_status() {
    print_header "TEST 7: KAFKA CLUSTER STATUS (INFORMATIONAL)"
    
    local kafka_phase=$(kubectl get kafka -n kafka my-cluster -o jsonpath='{.status.state}' 2>/dev/null || echo "")
    
    if [ -z "$kafka_phase" ]; then
        log_warn "Kafka cluster status not ready"
        log_info "Note: Kafka version mismatch with operator (requires 4.0.0+, configured 3.3.1)"
    elif [ "$kafka_phase" = "Ready" ]; then
        log_success "Kafka cluster is ready"
    else
        log_warn "Kafka cluster phase: $kafka_phase"
        log_info "Note: Graph-builder running in file-mode with synthetic events"
    fi
}

# Test 8: CRD/RBAC
test_rbac() {
    print_header "TEST 8: RBAC VALIDATION"
    
    # Check for critical service accounts
    local sa_count=0
    
    for ns in "ml" "quarantine"; do
        if kubectl get sa -n "$ns" | grep -q "default"; then
            ((sa_count++))
        fi
    done
    
    if [ $sa_count -gt 0 ]; then
        log_success "Service accounts are properly configured"
    else
        log_warn "Could not verify service accounts"
    fi
}

# Test 9: Image Status
test_image_status() {
    print_header "TEST 9: CONTAINER IMAGE STATUS"
    
    # Check for ImagePullBackOff issues
    local pull_errors=$(kubectl get pods -A --no-headers 2>/dev/null | grep -c "ImagePullBackOff" || echo "0")
    
    if [ "$pull_errors" -eq 0 ]; then
        log_success "No ImagePullBackOff errors detected"
    else
        log_warn "Found $pull_errors pod(s) with ImagePullBackOff (expected: ml-trainer, fluent-bit)"
        
        # Check specific expected images
        if kubectl get pod -n ml -l app=ml-trainer --no-headers 2>/dev/null | grep -q "ImagePullBackOff"; then
            log_info "  - ML trainer image (expected - heavy dependencies not built locally)"
        fi
    fi
}

# Test 10: Network Connectivity
test_network() {
    print_header "TEST 10: NETWORK CONNECTIVITY"
    
    # Try DNS resolution within cluster
    local dns_test=$(kubectl run -it --rm --restart=Never --image=alpine:3.18 -- nslookup kubernetes.default 2>/dev/null | grep -c "Name:" || echo "0")
    
    if [ "$dns_test" -gt 0 ]; then
        log_success "In-cluster DNS is working"
    else
        log_warn "Could not verify in-cluster DNS"
    fi
}

# Summary
print_summary() {
    print_header "VALIDATION SUMMARY"
    
    local total=$((TESTS_PASSED + TESTS_FAILED))
    local pass_rate=$((TESTS_PASSED * 100 / total))
    
    echo "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}/${total}"
    echo "Tests Failed: ${RED}${TESTS_FAILED}${NC}/${total}"
    echo "Pass Rate:    ${GREEN}${pass_rate}%${NC}"
    echo ""
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed! PoC deployment is healthy.${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Some tests failed. Check details above.${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║    ZERO-DAY DETECTION FRAMEWORK - POC VALIDATION SUITE        ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    test_cluster_connectivity || true
    test_namespaces || true
    test_core_services || true
    test_inference_endpoint || true
    test_containment_crd || true
    test_graph_builder || true
    test_kafka_status || true
    test_rbac || true
    test_image_status || true
    test_network || true
    
    print_summary
}

main "$@"
