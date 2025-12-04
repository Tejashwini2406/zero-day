"""Synthetic telemetry event generator for local testing."""
import argparse
import json
import random
import time
from datetime import datetime, timedelta


def gen_event(ts, pod, namespace, container_id, src_ip, dst_ip, src_port, dst_port, proto):
    return {
        "timestamp": ts.isoformat(),
        "event_type": "network.flow",
        "pod_name": pod,
        "namespace": namespace,
        "container_id": container_id,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": src_port,
        "dst_port": dst_port,
        "protocol": proto,
        "bytes": random.randint(40, 5000),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--start", type=str, default=None)
    args = parser.parse_args()

    start = datetime.utcnow() if args.start is None else datetime.fromisoformat(args.start)

    pods = [f"svc-{i}" for i in range(1, 6)]
    namespaces = ["dev", "prod"]

    with open(args.out, "w") as f:
        for i in range(args.count):
            ts = start + timedelta(seconds=i)
            pod = random.choice(pods)
            ns = random.choice(namespaces)
            container_id = f"cid-{random.randint(1,20)}"
            src_ip = f"10.0.{random.randint(0,3)}.{random.randint(2,250)}"
            dst_ip = f"10.0.{random.randint(0,3)}.{random.randint(2,250)}"
            ev = gen_event(ts, pod, ns, container_id, src_ip, dst_ip, random.randint(1024,65535), 80, "TCP")
            f.write(json.dumps(ev) + "\n")


if __name__ == "__main__":
    main()
