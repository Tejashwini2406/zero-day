# Temporal Graph Builder (PoC)

This microservice ingests normalized telemetry events (JSON) from Kafka or a file, sessionizes them into sliding time windows, and builds time-windowed graphs saved as Parquet files for downstream ML training.

Features:
- Supports input from a newline-delimited JSON file (local PoC) or Kafka topic.
- Sessionization by `container_id` and 5-tuple network flows.
- Builds NetworkX graphs per time window where nodes are pods/containers and edges are aggregated flows.
- Outputs per-window node and edge tables as Parquet files under an output directory.

Quick start (local file mode):

1. Create a virtualenv and install requirements:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Generate synthetic events and run the builder:
```bash
python -m graph_builder.synthetic_generator --out sample_events.jsonl --count 1000
python -m graph_builder.main --input-file sample_events.jsonl --out-dir ./graphs --window-size 60 --step 30
```

Outputs: `./graphs/` will contain Parquet files `window_*.nodes.parquet` and `window_*.edges.parquet`.

See `graph_builder` source for configuration options.
