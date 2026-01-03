#!/usr/bin/env python3
"""Lightweight dataset loader and IsolationForest baseline.

Usage:
  python ml/train_datasets.py --data-dir ./graphs --out-dir ./ml_artifacts --model isolation

The script looks for CSV/Parquet/JSONL files under `--data-dir`, extracts numeric columns,
fits an IsolationForest, and writes a simple report and model file.
"""
import argparse
import os
import glob
import json
from pathlib import Path

def discover_files(data_dir):
    exts = ["*.parquet", "*.csv", "*.jsonl", "*.json"]
    files = []
    for e in exts:
        files.extend(glob.glob(os.path.join(data_dir, "**", e), recursive=True))
    return sorted(files)

def load_table(path):
    import pandas as pd

    p = Path(path)
    if p.suffix == ".parquet":
        return pd.read_parquet(path)
    if p.suffix == ".csv":
        return pd.read_csv(path)
    if p.suffix in (".jsonl", ".json"):
        return pd.read_json(path, lines=True)
    raise RuntimeError(f"Unsupported file: {path}")

def train_isolation(df, out_dir, name="baseline"):
    from sklearn.ensemble import IsolationForest
    import joblib
    import numpy as np

    numeric = df.select_dtypes(include=["number"]).fillna(0)
    if numeric.shape[1] == 0 or numeric.shape[0] < 10:
        raise RuntimeError("Not enough numeric data to train baseline")

    clf = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
    clf.fit(numeric.values)
    scores = -clf.decision_function(numeric.values)  # higher = more anomalous

    os.makedirs(out_dir, exist_ok=True)
    model_path = os.path.join(out_dir, f"{name}_isoforest.joblib")
    joblib.dump(clf, model_path)

    report = {
        "n_samples": int(numeric.shape[0]),
        "n_features": int(numeric.shape[1]),
        "model": "IsolationForest",
        "model_path": model_path,
        "scores_sample": scores[:10].tolist(),
    }
    with open(os.path.join(out_dir, f"{name}_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(f"Trained IsolationForest saved to {model_path}")
    print(f"Report saved to {os.path.join(out_dir, name + '_report.json')}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="./data", help="Directory with datasets or graph files")
    p.add_argument("--out-dir", default="./ml_artifacts", help="Output directory for models/reports")
    p.add_argument("--model", choices=["isolation"], default="isolation")
    p.add_argument("--file", default=None, help="Optional single file to train on")
    args = p.parse_args()

    files = []
    if args.file:
        files = [args.file]
    else:
        files = discover_files(args.data_dir)

    if not files:
        print("No dataset files found. Use --file or put CSV/Parquet/JSONL under --data-dir")
        return

    # pick the first reasonable file
    for f in files:
        try:
            print(f"Loading {f}...")
            df = load_table(f)
            print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
            break
        except Exception as e:
            print(f"Skipping {f}: {e}")
            df = None
    if df is None:
        print("No usable files found.")
        return

    if args.model == "isolation":
        try:
            train_isolation(df, args.out_dir, name=Path(f).stem)
        except Exception as e:
            print(f"Training failed: {e}")

if __name__ == "__main__":
    main()
