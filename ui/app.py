from flask import Flask, render_template, jsonify, request
import kubernetes.client as k8s_client
import kubernetes.config as k8s_config
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Load Kubernetes config
try:
    k8s_config.load_incluster_config()
except:
    k8s_config.load_kube_config()

# Initialize K8s clients
v1 = k8s_client.CoreV1Api()
apps_v1 = k8s_client.AppsV1Api()
custom_api = k8s_client.CustomObjectsApi()

# Inference service URL (adjust for in-cluster)
INFERENCE_URL = os.getenv('INFERENCE_URL', 'http://inference-service.ml.svc.cluster.local:8080')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/system-status')
def system_status():
    """Get overall system status"""
    try:
        # Get pods in key namespaces
        namespaces = ['ml', 'kafka', 'monitoring', 'quarantine']
        status = {}

        for ns in namespaces:
            try:
                pods = v1.list_namespaced_pod(ns)
                status[ns] = {
                    'total': len(pods.items),
                    'running': len([p for p in pods.items if p.status.phase == 'Running']),
                    'failed': len([p for p in pods.items if p.status.phase == 'Failed'])
                }
            except:
                status[ns] = {'error': 'Namespace not found'}

        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get containment alerts (Containments CRs)"""
    try:
        # Mock alerts data for dummy UI
        mock_alerts = [
            {
                "metadata": {
                    "creationTimestamp": "2024-01-15T10:00:00Z",
                    "name": "alert-1"
                },
                "spec": {
                    "pod_name": "suspicious-pod-123",
                    "namespace": "default",
                    "action": "quarantine"
                }
            },
            {
                "metadata": {
                    "creationTimestamp": "2024-01-15T11:30:00Z",
                    "name": "alert-2"
                },
                "spec": {
                    "pod_name": "malicious-container-456",
                    "namespace": "ml",
                    "action": "isolate"
                }
            }
        ]
        return jsonify(mock_alerts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics')
def get_metrics():
    """Get model metrics from inference service"""
    try:
        # This would query the inference service for metrics
        # For now, return mock data
        return jsonify({
            'anomaly_score_avg': 0.15,
            'alerts_today': 3,
            'models_loaded': ['autoencoder', 'lstm_ae'],
            'last_training': '2024-01-15T10:00:00Z'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/graphs')
def get_graphs():
    """Get temporal graph data"""
    try:
        # This would read from graph-builder output (Parquet files)
        # For now, return mock data
        return jsonify({
            'nodes': 150,
            'edges': 450,
            'windows': 5,
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/<component>')
def get_logs(component):
    """Get logs from specific component"""
    try:
        # Map component to pod labels
        label_selectors = {
            'graph-builder': 'app=graph-builder',
            'inference': 'app=inference-service',
            'containment': 'app=containment-operator'
        }

        ns_map = {
            'graph-builder': 'ml',
            'inference': 'ml',
            'containment': 'quarantine'
        }

        if component not in label_selectors:
            return jsonify({'error': 'Invalid component'}), 400

        pods = v1.list_namespaced_pod(
            ns_map[component],
            label_selector=label_selectors[component]
        )

        if not pods.items:
            return jsonify({'logs': 'No pods found'})

        # Get logs from first pod
        logs = v1.read_namespaced_pod_log(
            pods.items[0].metadata.name,
            ns_map[component],
            tail_lines=100
        )

        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/score', methods=['POST'])
def score_request():
    """Proxy scoring requests to inference service"""
    try:
        data = request.json
        response = requests.post(f"{INFERENCE_URL}/score", json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
