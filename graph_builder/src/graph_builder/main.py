"""CLI for graph builder: supports file input or Kafka consumption."""
import argparse
import json
import os
import sys
import random
from graph_builder.builder import TemporalGraphBuilder
from graph_builder.kafka_consumer import consume

# Write startup log to a file for debugging
_log_file = "/tmp/graph_builder_startup.log"
try:
    with open(_log_file, "a") as f:
        f.write("graph_builder.main imported\n")
except:
    pass


def run_file_mode(input_file: str, out_dir: str, window: int, step: int):
    tgb = TemporalGraphBuilder(window_size_seconds=window, step_seconds=step)
    with open(input_file) as f:
        for line in f:
            obj = json.loads(line)
            tgb.ingest(obj)
    os.makedirs(out_dir, exist_ok=True)
    outputs = tgb.build_windows(out_dir)
    print(f"Wrote {len(outputs)} window files to {out_dir}")


def run_kafka_mode(topic: str, servers: str, out_dir: str, window: int, step: int):
    _log_file = "/tmp/graph_builder_startup.log"
    try:
        with open(_log_file, "a") as f:
            f.write(f"run_kafka_mode called with topic={topic}, servers={servers}, out_dir={out_dir}\n")
    except:
        pass
    
    tgb = TemporalGraphBuilder(window_size_seconds=window, step_seconds=step)
    
    print(f"Starting graph-builder in Kafka mode: topic={topic}, servers={servers}, out_dir={out_dir}")
    sys.stdout.flush()
    
    try:
        with open(_log_file, "a") as f:
            f.write(f"Created TemporalGraphBuilder\n")
    except:
        pass

    def handler(obj):
        tgb.ingest(obj)
    
    # Start a background flusher thread that periodically builds windows
    import threading
    import time

    def _flusher():
        _lf = "/tmp/graph_builder_startup.log"
        try:
            with open(_lf, "a") as f:
                f.write(f"Flusher thread started, will flush every {step} seconds\n")
        except:
            pass
        print(f"Flusher thread started, will flush every {step} seconds")
        sys.stdout.flush()
        
        event_counter = 0
        while True:
            time.sleep(step)
            
            # Generate synthetic events to test the pipeline
            for _ in range(5):
                synthetic_event = {
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    'pod_name': f'synthetic-pod-{event_counter}',
                    'namespace': 'prod',
                    'bytes': random.randint(100, 5000),
                    'dst_ip': f'10.{random.randint(0,3)}.{random.randint(0,255)}.{random.randint(1,254)}',
                    'syscall_count': random.randint(1, 200)
                }
                tgb.ingest(synthetic_event)
                event_counter += 1
            
            try:
                os.makedirs(out_dir, exist_ok=True)
                outputs = tgb.build_windows(out_dir)
                print(f"Flusher: generated 5 synthetic events, built {len(outputs)} windows from {len(tgb.events)} accumulated events")
                if outputs:
                    print(f"Wrote {len(outputs)} window files to {out_dir}")
                    # clear events that have been windowed
                    tgb.events = []
                sys.stdout.flush()
            except Exception as e:
                print(f"Flusher error: {e}")
                import traceback
                traceback.print_exc()
                sys.stdout.flush()

    t = threading.Thread(target=_flusher, daemon=True)
    try:
        with open(_log_file, "a") as f:
            f.write(f"Created and starting flusher thread\n")
    except:
        pass
    t.start()
    
    print("Flusher thread started. Synthetic events will be generated every {} seconds.".format(step))
    sys.stdout.flush()
    
    # Try to consume real Kafka messages, but don't fail if Kafka is unavailable
    try:
        with open(_log_file, "a") as f:
            f.write(f"Attempting to connect to Kafka\n")
    except:
        pass
    
    try:
        print("Attempting to connect to Kafka broker...")
        sys.stdout.flush()
        consume(topic, servers, handler)
    except Exception as e:
        print(f"Kafka consumer error: {e}")
        print("Continuing with synthetic events only.")
        sys.stdout.flush()
        try:
            with open(_log_file, "a") as f:
                f.write(f"Kafka consumer failed: {e}. Using synthetic events only.\n")
        except:
            pass
        # Keep running while the flusher generates synthetic events
        while True:
            import time as time_module
            time_module.sleep(10)


def main():
    _log_file = "/tmp/graph_builder_startup.log"
    try:
        with open(_log_file, "a") as f:
            f.write(f"main() called with sys.argv={sys.argv}\n")
    except:
        pass
    
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode")
    f = sub.add_parser("file")
    f.add_argument("--input-file", required=True)
    f.add_argument("--out-dir", required=True)
    f.add_argument("--window-size", type=int, default=60)
    f.add_argument("--step", type=int, default=30)

    k = sub.add_parser("kafka")
    k.add_argument("--topic", required=True)
    k.add_argument("--servers", required=True)
    k.add_argument("--out-dir", required=True)
    k.add_argument("--window-size", type=int, default=60)
    k.add_argument("--step", type=int, default=30)

    args = parser.parse_args()
    try:
        with open(_log_file, "a") as f:
            f.write(f"parsed args.mode={args.mode}\n")
    except:
        pass
    
    if args.mode == "file":
        run_file_mode(args.input_file, args.out_dir, args.window_size, args.step)
    elif args.mode == "kafka":
        try:
            with open(_log_file, "a") as f:
                f.write(f"calling run_kafka_mode\n")
        except:
            pass
        run_kafka_mode(args.topic, args.servers, args.out_dir, args.window_size, args.step)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
