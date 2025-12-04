"""Explainable AI (XAI) integration for anomaly explanations.

Uses SHAP for tabular features and a simplified feature attribution for graph models.
Produces human-readable explanations for detected anomalies.
"""

import torch
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
try:
    import shap
except ImportError:
    shap = None


class ShapExplainer:
    """SHAP-based explainer for tabular anomaly models (Autoencoder)."""
    
    def __init__(self, model, background_data: np.ndarray):
        """
        Args:
            model: PyTorch model (Autoencoder)
            background_data: background samples for SHAP (typically normal data)
        """
        self.model = model
        self.background = background_data
        if shap is not None:
            self.explainer = shap.DeepExplainer(model, torch.tensor(background_data, dtype=torch.float32))
        else:
            self.explainer = None

    def explain(self, sample: np.ndarray) -> Dict:
        """Explain prediction for a single sample."""
        if self.explainer is None:
            return {"error": "SHAP not installed"}
        
        x = torch.tensor(sample, dtype=torch.float32).unsqueeze(0)
        shap_values = self.explainer.shap_values(x)
        
        return {
            "feature_contributions": shap_values[0].tolist(),
            "base_value": float(self.explainer.expected_value),
        }


class GraphExplainer:
    """Simple graph-based explainer: identifies influential nodes/edges based on gradients."""
    
    def __init__(self, model):
        self.model = model

    def explain_anomaly(self, graph, node_idx: int) -> Dict:
        """Explain why a node is anomalous based on its neighborhood."""
        self.model.eval()
        graph.x.requires_grad_(True)
        
        with torch.enable_grad():
            recon, _ = self.model([graph])
            loss = (recon[node_idx] - graph.x[node_idx]).pow(2).sum()
            loss.backward()
        
        # Get gradients for node features
        feature_grads = graph.x.grad[node_idx].abs()
        
        # Get neighbors
        neighbors = []
        if hasattr(graph, 'edge_index') and graph.edge_index is not None:
            mask = (graph.edge_index[0] == node_idx) | (graph.edge_index[1] == node_idx)
            neighbors = graph.edge_index[:, mask].unique().tolist()
        
        return {
            "top_features": feature_grads.topk(3).indices.tolist(),
            "feature_importance": feature_grads.topk(3).values.tolist(),
            "neighboring_nodes": neighbors,
        }


class ExplanationGenerator:
    """Generates human-readable explanations for alerts."""
    
    def __init__(self, feature_names: List[str] = None):
        self.feature_names = feature_names or [
            "bytes_transferred",
            "unique_destinations",
            "flow_count",
            "syscall_rate",
            "error_rate",
        ]

    def generate_explanation(self, anomaly_score: float, attributions: Dict, mitre_mapping: str = None) -> str:
        """Generate human-friendly explanation text."""
        explanation = f"Anomaly score: {anomaly_score:.4f}. "
        
        if "feature_contributions" in attributions:
            top_features = attributions.get("top_features", [])
            if top_features:
                feature_names = [self.feature_names[i] if i < len(self.feature_names) else f"feature_{i}" for i in top_features]
                explanation += f"Key indicators: {', '.join(feature_names)}. "
        
        if "feature_importance" in attributions:
            explanation += f"Anomaly patterns align with abnormal {attributions['feature_importance']}. "
        
        if mitre_mapping:
            explanation += f"Potential MITRE ATT&CK: {mitre_mapping}. "
        
        return explanation


class MitreMapper:
    """Maps detected patterns to MITRE ATT&CK techniques."""
    
    # Simple pattern-to-technique mapping
    PATTERNS = {
        "high_syscall_rate": "T1059",  # Command execution
        "setuid_or_capabilities": "T1548.001",  # Privilege escalation
        "network_exfil": "T1041",  # Exfiltration over network
        "process_creation_burst": "T1059",  # Command/script execution
        "container_socket_mount": "T1610",  # Container escape
        "lateral_rpc": "T1021",  # Lateral movement
    }

    def map_features_to_technique(self, features: Dict) -> str:
        """Map feature patterns to MITRE ATT&CK technique."""
        for pattern, technique in self.PATTERNS.items():
            if pattern in features.get("detected_patterns", []):
                return technique
        return "Unknown"
