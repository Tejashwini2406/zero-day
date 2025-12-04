# Runbook: Zero-Day Detection & Mitigation Framework

## Quick Reference

- **Dashboard**: http://localhost:3000 (port-forward to kube-prometheus-grafana service)
- **Inference API**: http://ml-inference:8080 (score windows)
- **Containment Operator**: quarantine namespace
- **Logs**: kubectl logs -n [namespace] [pod]

## Incident Response Workflow

### 1. Alert Triggered
When `anomaly_score > 0.9` for a pod:

```bash
# Check the alert in Grafana or Alertmanager
kubectl get alerts -A

# Check inference service logs
kubectl -n ml logs -f deploy/inference-service
```

### 2. Review Explanation
```bash
# Get the Containment CR with explanation
kubectl get containment -A -o json | jq '.items[] | {pod: .spec.alertID, confidence: .spec.confidence, explanation: .spec.explanation}'
```

### 3. Approve Containment (if needed)
```bash
# Patch Containment CR to approve (add approvalToken)
kubectl patch containment alert-pod -p '{"spec":{"approvalToken":"approved"}}'
```

### 4. Monitor Action Application
```bash
# Check if containment action was applied
kubectl get containment -o wide

# Verify NetworkPolicy was created
kubectl get networkpolicies -A
```

### 5. Analyze False Positives
```bash
# Check false positive rate
kubectl -n monitoring port-forward svc/kube-prometheus-grafana 3000:80
# Open http://localhost:3000 → Zero-Day Detection Dashboard → False Positive Rate panel

# If high, retrain model:
make train-ml
```

## Model Retraining Workflow

### Trigger Manual Retraining
```bash
# Collect recent windows
kubectl -n ml logs deploy/graph-builder > recent_events.log

# Retrain baselines
cd ml && bash run_full_train.sh ./new_models

# Update inference service with new model
kubectl set image deployment/inference-service inference=inference:v2.0
```

### Monitor Training Job
```bash
kubectl -n ml logs -f job/ml-trainer-[job-id]
```

## Containment Action Rollback

If a containment action causes disruption:

```bash
# Delete the NetworkPolicy isolation
kubectl delete networkpolicy isolate-[pod-name] -n [namespace]

# Or update Containment CR to mark rollback
kubectl patch containment alert-[pod-name] -p '{"status":{"state":"rolled_back"}}'
```

## Troubleshooting

### Inference Service Not Responding
```bash
# Check if model is loaded
kubectl -n ml logs deploy/inference-service | grep "Model loaded"

# Restart service if needed
kubectl -n ml rollout restart deploy/inference-service
```

### Graph Builder Not Consuming Kafka
```bash
# Check Kafka cluster status
kubectl -n kafka get kafka
kubectl -n kafka get pods

# Check graph-builder pod logs
kubectl -n ml logs -f deploy/graph-builder

# Verify Kafka topic exists and has data
kubectl -n kafka run kafka-client --image=strimzi/kafka:latest --restart=Never -- \
  bin/kafka-console-consumer.sh --bootstrap-server my-cluster-kafka-bootstrap:9092 --topic telemetry.logs --max-messages 5
```

### High Containment Failure Rate
```bash
# Check operator logs
kubectl -n quarantine logs -f deploy/containment-operator

# Check RBAC permissions
kubectl get rolebindings -n quarantine -o yaml
```

## Performance Tuning

### Reduce Inference Latency
- Increase inference service replicas: `kubectl scale deploy/inference-service --replicas=3 -n ml`
- Use GPU if available: modify inference deployment to request GPU

### Reduce False Positives
- Increase anomaly threshold: edit inference deployment env var `ANOMALY_THRESHOLD=0.85`
- Retrain model with more normal data

### Reduce Memory Usage
- Lower graph window size: `--window-size 30` in graph-builder args
- Use model quantization for inference

## Testing

### Test Inference Service
```bash
kubectl -n ml port-forward svc/inference 8080:8080

curl -X POST http://localhost:8080/score \
  -H "Content-Type: application/json" \
  -d '{
    "pod_name": "test-pod",
    "namespace": "dev",
    "features": [0.1, -0.2, 0.3, 0.0, 0.1, 0.2, -0.1, 0.0, 0.05, -0.05, 0.1, 0.2, 0.05, -0.1, 0.15, 0.0]
  }'
```

### Test Containment Operator
```bash
# Create a test Containment CR
kubectl apply -f - << EOF
apiVersion: security.example.com/v1alpha1
kind: Containment
metadata:
  name: test-containment
  namespace: dev
spec:
  alertID: alert-test-pod
  confidence: 0.95
  suggestedAction: isolate_pod
  dryRun: true
  approvalToken: test
EOF

# Check status
kubectl get containment test-containment -o json | jq '.status'
```

## Metrics & KPIs

Monitor these key metrics in Grafana:

1. **Detection Latency** (MTTD): anomaly_detection_latency_seconds (target: < 30s)
2. **False Positive Rate**: false_positive_rate (target: < 5%)
3. **Inference Throughput**: inference_requests_per_second (target: > 100 req/s)
4. **Containment Success Rate**: containment_success_rate (target: > 95%)
5. **Model Drift**: model_prediction_std_dev (alert if trending up)

## Escalation Matrix

| Severity | Issue | Action |
|----------|-------|--------|
| Critical | Containment operator down | Restart deployment, check logs, page on-call |
| Critical | Inference service errors | Rollback model, check inference logs |
| High | High false positive rate (>10%) | Retrain model, increase threshold |
| High | Graph builder lag | Check Kafka, increase replicas |
| Medium | Inference latency > 100ms | Scale inference replicas |
| Low | Dashboard unavailable | Restart Grafana |

## References

- MITRE ATT&CK Framework: https://attack.mitre.org/
- Kubernetes Security: https://kubernetes.io/docs/concepts/security/
- Istio Security: https://istio.io/latest/docs/concepts/security/
- OpenTelemetry: https://opentelemetry.io/

---

**Last Updated**: 2025-11-12  
**Owner**: Security Engineering  
**On-Call**: See PagerDuty
