#!/usr/bin/env python3
"""
Produce synthetic security events to Kafka topic for testing.
"""
import json
import sys
import random
from datetime import datetime
from kafka import KafkaProducer

def main():
    try:
        import os
        use_kafka = os.getenv('USE_KAFKA', 'false').lower() in ('1','true','yes')
        if use_kafka:
            bootstrap = os.getenv('KAFKA_BOOTSTRAP', 'localhost:9092')
            producer = KafkaProducer(
                bootstrap_servers=[bootstrap],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            print("✓ Connected to Kafka broker", file=sys.stderr)
        else:
            outpath = os.getenv('EVENTS_FILE', '/workspace/events.jsonl')
            print(f"✓ Writing events to file mode: {outpath}", file=sys.stderr)

        event_count = int(os.getenv('EVENT_COUNT', '100'))
        written = 0
        for i in range(event_count):
            ts = datetime.utcnow().isoformat() + 'Z'
            event = {
                'timestamp': ts,
                'pod_name': f'app-{random.randint(1, 5)}',
                'namespace': 'production',
                'bytes': random.randint(100, 10000),
                'dst_ip': f'192.168.{random.randint(0, 255)}.{random.randint(1, 254)}',
                'syscall_count': random.randint(5, 100),
                'alert_level': random.choice(['low', 'medium', 'high'])
            }

            if use_kafka:
                future = producer.send('security-events', value=event)
                try:
                    future.get(timeout=10)
                    print(f"✓ Event {i+1}/{event_count} sent", file=sys.stderr)
                except Exception as e:
                    print(f"✗ Failed to send event {i+1}: {e}", file=sys.stderr)
            else:
                # append to file
                with open(outpath, 'a') as f:
                    f.write(json.dumps(event) + "\n")
                written += 1

        if use_kafka:
            producer.flush()
            producer.close()
            print(f"✓ Produced {event_count} events to 'security-events' topic", file=sys.stderr)
        else:
            print(f"✓ Wrote {written} events to {outpath}", file=sys.stderr)

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
