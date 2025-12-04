#!/usr/bin/env python3
"""Minimal training harness skeleton for TGNN (demo only)."""
import argparse
import torch
from ml.tgnn.model import TemporalGNN

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--epochs', type=int, default=1)
    args = p.parse_args()

    # toy example: random tensors (real pipeline should convert Parquet -> PyG datasets)
    model = TemporalGNN(in_channels=8)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    for epoch in range(args.epochs):
        model.train()
        # fake batch
        x = torch.randn((16,8))
        edge_index = torch.randint(0,16,(2,32))
        batch = torch.zeros(16, dtype=torch.long)
        out = model(x, edge_index, batch)
        loss = out.abs().mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        print(f"Epoch {epoch} loss={loss.item():.4f}")

if __name__=='__main__':
    main()
