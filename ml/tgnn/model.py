import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv, global_mean_pool

class TemporalGNN(nn.Module):
    def __init__(self, in_channels, hidden=64, out_channels=32):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden)
        self.conv2 = GCNConv(hidden, hidden)
        self.fc = nn.Sequential(nn.Linear(hidden, out_channels), nn.ReLU())

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()
        x = global_mean_pool(x, batch)
        return self.fc(x)
