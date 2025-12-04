#!/usr/bin/env python3
"""Lightweight XAI explainer for node parquet windows.

This script is intentionally simple and dependency-light: it uses pandas/numpy
to compute per-node feature deviations from a baseline mean and reports a
proportional contribution per numeric feature. It's a demonstrative XAI step
for the PoC (not a production SHAP implementation).
"""
import argparse
import json
import os
import pandas as pd
import numpy as np


def explain_nodes(nodes_parquet_path, out_path=None, top_k=5):
    df = pd.read_parquet(nodes_parquet_path)
    # Select numeric columns only
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not num_cols:
        raise RuntimeError("No numeric columns found in parquet to explain")

    # Compute baseline mean per feature
    means = df[num_cols].mean()
    # Per-node absolute deviation from mean
    abs_dev = (df[num_cols] - means).abs()
    # Per-node total deviation score
    total_dev = abs_dev.sum(axis=1)
    # Avoid divide by zero
    total_dev = total_dev.replace(0, 1e-12)

    explanations = []
    for idx, row in df.iterrows():
        node_id = None
        # choose a reasonable node identifier if present
        for candidate in ("id", "node_id", "pod_name", "name"):
            if candidate in df.columns:
                node_id = row.get(candidate)
                break
        if node_id is None:
            node_id = int(idx)

        feats = {}
        for c in num_cols:
            contribution = float(abs_dev.at[idx, c])
            feats[c] = {
                "value": float(row[c]),
                "baseline_mean": float(means[c]),
                "abs_dev": contribution,
                "pct": float(contribution / total_dev.at[idx])
                if total_dev.at[idx] != 0 else 0.0,
            }

        explanations.append({
            "node": str(node_id),
            "score": float(total_dev.at[idx]),
            "features": feats,
        })

    # sort by score desc and keep top_k
    explanations.sort(key=lambda x: x["score"], reverse=True)
    result = {
        "window": os.path.basename(nodes_parquet_path),
        "top_nodes": explanations[:top_k],
    }

    if out_path is None:
        out_path = nodes_parquet_path + ".xai.json"

    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Wrote XAI explanation to {out_path}")
    return out_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("nodes", help="Path to nodes parquet file")
    p.add_argument("--out", help="Output JSON path (optional)")
    p.add_argument("--top-k", type=int, default=5)
    args = p.parse_args()
    explain_nodes(args.nodes, args.out, args.top_k)


if __name__ == '__main__':
    main()
