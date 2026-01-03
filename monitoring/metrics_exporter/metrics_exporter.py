#!/usr/bin/env python3
"""Simple demo exporter that exposes expected Prometheus metrics.

It simulates event traffic and watches for `attack_events.jsonl` to increase alert counters.
"""
import time
import os
import random
import json
from prometheus_client import start_http_server, Counter, Gauge, Histogram

EVENTS = Counter('zero_day_events_total', 'Total synthetic events')
ALERTS = Counter('zero_day_attack_alerts_total', 'Total attack alerts injected')
ATTACK_SCORE = Gauge('zero_day_attack_score', 'Current attack score (0-100)')
PROC_LATENCY = Histogram('graph_builder_processing_duration_seconds', 'Processing durations')

ATTACK_FILE = '/workspace/attack_events.jsonl'
EVENTS_FILE = '/workspace/events.jsonl'
STATE_FILE = '/tmp/exporter_state.json'


def load_state():
    """Load persisted state"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'seen_attack_lines': 0, 'seen_event_lines': 0}


def save_state(state):
    """Save state to disk"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except:
        pass


def process_file_lines(path, seen_lines):
    if not os.path.exists(path):
        return seen_lines, 0
    count = 0
    try:
        with open(path, 'r') as f:
            for i, _ in enumerate(f, 1):
                pass
        count = i if 'i' in locals() else 0
    except Exception:
        count = 0
    if count > seen_lines:
        delta = count - seen_lines
        print(f"[{path}] Found {count} lines (was {seen_lines}), delta={delta}")
        return count, delta
    return seen_lines, 0


def process_attack_file(seen_lines):
    seen_lines, delta = process_file_lines(ATTACK_FILE, seen_lines)
    if delta > 0:
        ALERTS.inc(delta)
    return seen_lines, delta


def process_events_file(seen_lines):
    seen_lines, delta = process_file_lines(EVENTS_FILE, seen_lines)
    if delta > 0:
        EVENTS.inc(delta)
    return seen_lines, delta

def main():
    start_http_server(8000)
    print('Metrics exporter running on :8000')
    
    # Load state from disk
    state = load_state()
    seen_attack_lines = state['seen_attack_lines']
    seen_event_lines = state['seen_event_lines']
    print(f'Loaded state: seen_attack_lines={seen_attack_lines}, seen_event_lines={seen_event_lines}')
    
    last_attack_time = 0
    while True:
        # simulate incoming events
        inc = random.randint(1, 10)
        EVENTS.inc(inc)
        # simulate processing latency samples
        for _ in range(random.randint(1,3)):
            PROC_LATENCY.observe(random.random()*0.5)

        # detect events and attacks files and update metrics
        seen_attack_lines, attack_delta = process_attack_file(seen_attack_lines)
        seen_event_lines, event_delta = process_events_file(seen_event_lines)

        now = time.time()
        if attack_delta > 0:
            last_attack_time = now
            ATTACK_SCORE.set(min(100, 50 + attack_delta))
        else:
            # decay attack score over time
            if now - last_attack_time > 30:
                ATTACK_SCORE.set(max(0, ATTACK_SCORE._value.get() - 1))
        
        # Save state periodically
        state = {'seen_attack_lines': seen_attack_lines, 'seen_event_lines': seen_event_lines}
        save_state(state)

        time.sleep(1)

if __name__ == '__main__':
    main()

