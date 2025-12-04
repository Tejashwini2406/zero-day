"""Temporal Graph Builder: sessionizes events into sliding windows and emits graph tables."""
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

import networkx as nx
import pandas as pd


def parse_ts(s: str) -> datetime:
    # Support ISO timestamps with optional trailing 'Z' (UTC) and numeric timestamps
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return datetime.fromtimestamp(s)
    s = s.rstrip("Z")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        # Fallback: try parsing common formats
        try:
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None


class TemporalGraphBuilder:
    def __init__(self, window_size_seconds=60, step_seconds=30):
        self.window_size = timedelta(seconds=window_size_seconds)
        self.step = timedelta(seconds=step_seconds)
        self.events: List[Dict] = []

    def ingest(self, event: Dict):
        # Expect event with ISO timestamp
        event["_ts"] = parse_ts(event.get("timestamp")) if isinstance(event.get("timestamp"), str) else parse_ts(event.get("timestamp")) if event.get("timestamp") is not None else None
        # Also compute numeric epoch to make sorting robust
        try:
            event["_ts_epoch"] = event["_ts"].timestamp() if event.get("_ts") is not None else None
        except Exception:
            event["_ts_epoch"] = None
        self.events.append(event)

    def _window_bounds(self, start: datetime, end: datetime):
        cur = start
        while cur + self.window_size <= end:
            yield cur, cur + self.window_size
            cur += self.step

    def build_windows(self, out_dir: str):
        if not self.events:
            return []
        # Drop events with unparsable timestamps
        self.events = [e for e in self.events if e.get("_ts") is not None]
        if not self.events:
            return []
        # Prefer numeric epoch if present for sorting
        self.events.sort(key=lambda e: e.get("_ts_epoch") if e.get("_ts_epoch") is not None else e.get("_ts"))
        start = self.events[0]["_ts"]
        end = self.events[-1]["_ts"] + timedelta(seconds=1)
        outputs = []
        for wstart, wend in self._window_bounds(start, end):
            window_events = [e for e in self.events if wstart <= e["_ts"] < wend]
            if not window_events:
                continue
            nodes_table, edges_table = self._build_graph_tables(window_events, wstart, wend)
            # save to parquet
            nodes_path = f"{out_dir}/window_{int(wstart.timestamp())}.nodes.parquet"
            edges_path = f"{out_dir}/window_{int(wstart.timestamp())}.edges.parquet"
            # Specify fastparquet engine explicitly to avoid pyarrow/pandas compatibility issues
            nodes_table.to_parquet(nodes_path, index=False, engine="fastparquet")
            edges_table.to_parquet(edges_path, index=False, engine="fastparquet")
            outputs.append((nodes_path, edges_path))
        return outputs

    def _build_graph_tables(self, events: List[Dict], wstart: datetime, wend: datetime):
        # Nodes are pods/containers
        node_features = defaultdict(lambda: {"pod_name": None, "namespace": None, "bytes": 0, "outgoing_unique_dst": set(), "flow_count": 0})
        edge_features = defaultdict(lambda: {"bytes": 0, "count": 0})

        for e in events:
            pod = e.get("pod_name") or e.get("container_id") or "unknown"
            ns = e.get("namespace", "default")
            node = pod
            node_features[node]["pod_name"] = pod
            node_features[node]["namespace"] = ns
            node_features[node]["bytes"] += int(e.get("bytes", 0))
            node_features[node]["outgoing_unique_dst"].add(e.get("dst_ip"))
            node_features[node]["flow_count"] += 1

            src = pod
            dst = e.get("dst_ip") or "ip-unknown"
            edge_key = (src, dst)
            edge_features[edge_key]["bytes"] += int(e.get("bytes", 0))
            edge_features[edge_key]["count"] += 1

        # Build pandas tables
        nodes_rows = []
        for node, feats in node_features.items():
            nodes_rows.append({
                "node_id": node,
                "pod_name": feats["pod_name"],
                "namespace": feats["namespace"],
                "bytes": feats["bytes"],
                "outgoing_unique_dst_count": len(feats["outgoing_unique_dst"]),
                "flow_count": feats["flow_count"],
                "window_start": wstart.isoformat(),
                "window_end": wend.isoformat(),
            })

        edges_rows = []
        for (src, dst), feats in edge_features.items():
            edges_rows.append({
                "src": src,
                "dst": dst,
                "bytes": feats["bytes"],
                "count": feats["count"],
                "window_start": wstart.isoformat(),
                "window_end": wend.isoformat(),
            })

        nodes_df = pd.DataFrame(nodes_rows)
        edges_df = pd.DataFrame(edges_rows)
        return nodes_df, edges_df


if __name__ == "__main__":
    print("TemporalGraphBuilder module. Use from python code or via main CLI.")
