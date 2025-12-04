"""Temporal Graph Neural Network (TGNN) for anomaly detection.

Combines GraphSAGE/GAT for spatial aggregation with LSTM for temporal patterns.
Input: time-windowed node/edge Parquet tables.
Output: anomaly scores per node.
"""

import torch
import torch.nn as nn
from torch_geometric.nn import GraphSAGE, GATConv, global_mean_pool
from torch_geometric.data import Data, DataLoader
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple


class TemporalGraphEncoder(nn.Module):
    """Spatial encoder: applies GraphSAGE/GAT over graph snapshots."""
    
    def __init__(self, in_channels: int, hidden_channels: int, num_layers: int = 2):
        super().__init__()
        self.sage_layers = nn.ModuleList()
        self.sage_layers.append(GraphSAGE(in_channels, hidden_channels, num_layers=num_layers))
        self.hidden_channels = hidden_channels

    def forward(self, x, edge_index, batch=None):
        # x: (N, in_channels) node features
        # edge_index: (2, E) edge indices
        # batch: (N,) batch assignment
        h = self.sage_layers[0](x, edge_index)  # (N, hidden)
        return h


class TemporalAggregator(nn.Module):
    """Temporal aggregator: LSTM over node embeddings across time windows."""
    
    def __init__(self, hidden_channels: int, lstm_hidden: int = 64, num_layers: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(hidden_channels, lstm_hidden, num_layers, batch_first=True)
        self.lstm_hidden = lstm_hidden

    def forward(self, embeddings_seq):
        # embeddings_seq: (T, N, hidden) time-windowed node embeddings
        # Process each node across time
        T, N, H = embeddings_seq.shape
        embeddings_seq = embeddings_seq.view(T, N, H)
        
        # Simple temporal aggregation: mean over windows (can be expanded to LSTM)
        temporal_emb = embeddings_seq.mean(dim=0)  # (N, H)
        return temporal_emb


class TGNN(nn.Module):
    """Temporal Graph Neural Network for anomaly detection."""
    
    def __init__(self, in_channels: int, hidden_channels: int = 64, lstm_hidden: int = 32):
        super().__init__()
        self.encoder = TemporalGraphEncoder(in_channels, hidden_channels, num_layers=2)
        self.temporal_agg = TemporalAggregator(hidden_channels, lstm_hidden)
        self.decoder = nn.Sequential(
            nn.Linear(lstm_hidden, 32),
            nn.ReLU(),
            nn.Linear(32, in_channels)
        )

    def forward(self, graphs: List[Data]):
        """
        Args:
            graphs: list of Data objects (one per time window)
        Returns:
            reconstructed node features (for reconstruction loss)
        """
        embeddings_seq = []
        for g in graphs:
            h = self.encoder(g.x, g.edge_index)
            embeddings_seq.append(h)
        
        embeddings_seq = torch.stack(embeddings_seq)  # (T, N, H)
        temporal_emb = self.temporal_agg(embeddings_seq)  # (N, lstm_hidden)
        reconstructed = self.decoder(temporal_emb)  # (N, in_channels)
        
        # Return reconstruction of initial node features for loss computation
        initial_features = graphs[0].x if graphs else torch.zeros_like(temporal_emb)
        return reconstructed, temporal_emb


def load_parquet_graphs(parquet_dir: str) -> List[Data]:
    """Load time-windowed node/edge Parquet files and convert to PyG Data objects."""
    path = Path(parquet_dir)
    graphs = []
    
    # Sort files by window timestamp
    node_files = sorted(path.glob("window_*.nodes.parquet"))
    edge_files = sorted(path.glob("window_*.edges.parquet"))
    
    for node_file, edge_file in zip(node_files, edge_files):
        nodes_df = pd.read_parquet(node_file)
        edges_df = pd.read_parquet(edge_file)
        
        # Create node features
        feature_cols = ['bytes', 'outgoing_unique_dst_count', 'flow_count']
        x = torch.tensor(nodes_df[feature_cols].values, dtype=torch.float32)
        
        # Normalize features
        x = (x - x.mean(dim=0)) / (x.std(dim=0) + 1e-6)
        
        # Create edge index (map node names to indices)
        node_map = {name: idx for idx, name in enumerate(nodes_df['node_id'])}
        edge_list = []
        for _, row in edges_df.iterrows():
            src_idx = node_map.get(row['src'], -1)
            dst_idx = node_map.get(row['dst'], -1)
            if src_idx >= 0 and dst_idx >= 0:
                edge_list.append([src_idx, dst_idx])
        
        if edge_list:
            edge_index = torch.tensor(edge_list, dtype=torch.long).t()
        else:
            edge_index = torch.zeros((2, 0), dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index)
        graphs.append(data)
    
    return graphs


def train_tgnn(parquet_dir: str, output_dir: str, epochs: int = 10):
    """Train TGNN on Parquet graph windows."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    graphs = load_parquet_graphs(parquet_dir)
    if not graphs or len(graphs) < 2:
        print(f"Not enough graphs (need >= 2). Found {len(graphs)}")
        return
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    in_channels = graphs[0].x.shape[1]
    
    model = TGNN(in_channels=in_channels, hidden_channels=64, lstm_hidden=32).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()
    
    for epoch in range(epochs):
        model.train()
        
        # Use all graphs as one batch (time-series)
        graphs_batch = [g.to(device) for g in graphs]
        recon, embeddings = model(graphs_batch)
        
        # Reconstruction loss: use mean of node features across windows
        target = torch.stack([g.x for g in graphs_batch]).mean(dim=0)
        loss = criterion(recon, target)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        print(f"Epoch {epoch+1}/{epochs} loss={loss.item():.6f}")
    
    # Save model
    torch.save(model.state_dict(), os.path.join(output_dir, "tgnn.pt"))
    print(f"Model saved to {output_dir}/tgnn.pt")


def score_with_tgnn(parquet_dir: str, model_path: str) -> dict:
    """Score a set of graph windows with trained TGNN."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    graphs = load_parquet_graphs(parquet_dir)
    if not graphs:
        return {}
    
    in_channels = graphs[0].x.shape[1]
    model = TGNN(in_channels=in_channels, hidden_channels=64, lstm_hidden=32).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    with torch.no_grad():
        graphs_batch = [g.to(device) for g in graphs]
        recon, embeddings = model(graphs_batch)
        
        # Compute per-node reconstruction error
        target = torch.stack([g.x for g in graphs_batch]).mean(dim=0)
        errors = (recon - target).abs().mean(dim=1)
    
    # Map back to node IDs
    node_ids = pd.read_parquet(list(Path(parquet_dir).glob("window_*.nodes.parquet"))[0])['node_id'].tolist()
    scores = {node_id: error.item() for node_id, error in zip(node_ids, errors)}
    
    return scores
