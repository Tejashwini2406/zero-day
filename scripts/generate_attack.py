#!/usr/bin/env python3
"""Generate synthetic attack events as JSONL for graph-builder file mode."""
import json
import random
from datetime import datetime, timedelta
import argparse

def gen_event(t, pod_name, namespace, dst_ip, bytes_val, syscall_count):
    return {
        "timestamp": t.isoformat() + "Z",
        "pod_name": pod_name,
        "namespace": namespace,
        "bytes": bytes_val,
        "dst_ip": dst_ip,
        "syscall_count": syscall_count,
    }

def generate(path, count=200, attack_start=120, attack_burst=50):
    start = datetime.utcnow() - timedelta(seconds=count)
    events = []
    # baseline traffic
    for i in range(count):
        t = start + timedelta(seconds=i)
        pod = f"app-{random.randint(1,8)}"
        dst = f"10.{random.randint(0,3)}.{random.randint(0,255)}.{random.randint(1,254)}"
        events.append(gen_event(t, pod, "prod", dst, random.randint(100,2000), random.randint(1,20)))

    # inject attack: burst of execs/large bytes from one pod
    attack_time = start + timedelta(seconds=attack_start)
    attacker = "compromised-pod"
    for i in range(attack_burst):
        t = attack_time + timedelta(milliseconds=i*50)
        events.append(gen_event(t, attacker, "prod", "203.0.113.45", random.randint(4000,20000), random.randint(50,300)))

    # sort and write
    events.sort(key=lambda e: e["timestamp"])
    with open(path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    print(f"Wrote {len(events)} events to {path}")

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="attack_events.jsonl")
    p.add_argument("--count", type=int, default=400)
    p.add_argument("--attack-start", type=int, default=120)
    p.add_argument("--attack-burst", type=int, default=60)
    args = p.parse_args()
    generate(args.out, args.count, args.attack_start, args.attack_burst)
