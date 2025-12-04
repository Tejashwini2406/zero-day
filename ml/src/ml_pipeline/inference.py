"""Inference microservice: loads trained models, scores windows, emits Alert CRs."""
import os
import json
import numpy as np
from pathlib import Path
from flask import Flask, request, jsonify
from kubernetes import client, config
try:
    import torch
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

if TORCH_AVAILABLE:
    from ml_pipeline.models import Autoencoder
    from ml_pipeline.data import SequenceDataset
else:
    # Lightweight fallbacks when torch is not available in the runtime image
    Autoencoder = None
    SequenceDataset = None

app = Flask(__name__)

# Load config
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CustomObjectsApi()
MODEL_PATH = os.getenv("MODEL_PATH", "/models/autoencoder.pt")


def load_model(path):
    """Load trained model."""
    if not os.path.exists(path):
        return None
    if not TORCH_AVAILABLE or Autoencoder is None:
        print("Torch not available in inference image; skipping model load.")
        return None
    model = Autoencoder(input_dim=16, hidden_dims=[64, 32])
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model


def score_window(model, window_features):
    """Compute anomaly score (reconstruction error)."""
    # If model is available use reconstruction error; otherwise use a simple heuristic
    if model is not None and TORCH_AVAILABLE:
        with torch.no_grad():
            x = torch.tensor(window_features, dtype=torch.float32).unsqueeze(0)
            recon = model(x)
            loss = torch.nn.MSELoss()(recon, x).item()
        return float(loss)
    else:
        # Heuristic anomaly score: normalized L2 norm of features
        arr = np.array(window_features, dtype=np.float32)
        score = float(np.linalg.norm(arr) / (np.sqrt(len(arr)) + 1e-6))
        return score


def create_alert(pod_name, namespace, score, explanation):
    """Create and submit Alert CRD to Kubernetes."""
    alert = {
        "apiVersion": "security.example.com/v1alpha1",
        "kind": "Containment",
        "metadata": {
            "name": f"alert-{pod_name}-{int(score*1000)}",
            "namespace": namespace,
        },
        "spec": {
            "alertID": f"alert-{pod_name}",
            "confidence": min(0.99, score),
            "suggestedAction": "isolate_pod",
            "dryRun": False,
            "explanation": explanation,
        },
    }
    try:
        v1.create_namespaced_custom_object(
            group="security.example.com",
            version="v1alpha1",
            namespace=namespace,
            plural="containments",
            body=alert,
        )
        return True
    except Exception as e:
        print(f"Error creating alert: {e}")
        return False


@app.route("/score", methods=["POST"])
def score():
    """Score a window: expects JSON with node features."""
    try:
        data = request.json
        model = load_model(MODEL_PATH)
        features = np.array(data.get("features"), dtype=np.float32)
        # If model isn't available, score_window will use a heuristic fallback
        score = score_window(model, features)
        # If score > threshold, emit alert
        threshold = float(os.getenv("ANOMALY_THRESHOLD", "0.5"))
        if score > threshold:
            pod = data.get("pod_name", "unknown")
            ns = data.get("namespace", "default")
            create_alert(pod, ns, score, f"High reconstruction error: {score:.4f}")
        return jsonify({"score": score, "anomaly": score > threshold})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
