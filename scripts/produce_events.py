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
        producer = KafkaProducer(
            bootstrap_servers=['my-cluster-kafka-bootstrap.kafka.svc:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )
        
        print("✓ Connected to Kafka broker", file=sys.stderr)
        
        event_count = 100
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
            
            future = producer.send('security-events', value=event)
            try:
                future.get(timeout=10)
                print(f"✓ Event {i+1}/{event_count} sent", file=sys.stderr)
            except Exception as e:
                print(f"✗ Failed to send event {i+1}: {e}", file=sys.stderr)
        
        producer.flush()
        producer.close()
        print(f"✓ Produced {event_count} events to 'security-events' topic", file=sys.stderr)
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
