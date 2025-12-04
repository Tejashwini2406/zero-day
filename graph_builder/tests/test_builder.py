import os
import tempfile
import json
from graph_builder.synthetic_generator import gen_event
from graph_builder.builder import TemporalGraphBuilder
from datetime import datetime, timedelta


def test_builder_window(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    tgb = TemporalGraphBuilder(window_size_seconds=10, step_seconds=5)
    start = datetime.utcnow()
    # create events spanning 20 seconds for two pods
    for i in range(20):
        ts = start + timedelta(seconds=i)
        ev = {
            "timestamp": ts.isoformat(),
            "pod_name": "svc-1" if i%2==0 else "svc-2",
            "namespace": "dev",
            "container_id": f"cid-{i%3}",
            "dst_ip": "10.0.0.5",
            "bytes": 100 + i,
        }
        tgb.ingest(ev)

    outputs = tgb.build_windows(str(out_dir))
    # Expect at least one output window
    assert len(outputs) >= 1
    # check files exist
    for nodes_path, edges_path in outputs:
        assert os.path.exists(nodes_path)
        assert os.path.exists(edges_path)
