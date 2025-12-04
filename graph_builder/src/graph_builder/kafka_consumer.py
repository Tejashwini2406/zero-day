"""Optional Kafka consumer wrapper to feed events into the builder."""
from kafka import KafkaConsumer
import json
from typing import Callable
import sys
import time


def consume(topic: str, bootstrap_servers: str, handler: Callable[[dict], None], group_id: str = None):
    _log_file = "/tmp/graph_builder_startup.log"
    
    # Use a unique group_id based on timestamp to ensure fresh reads
    if group_id is None:
        import socket
        hostname = socket.gethostname()
        group_id = f"graph-builder-{hostname}-{int(time.time())}"
    
    try:
        with open(_log_file, "a") as f:
            f.write(f"consume() called with topic={topic}, bootstrap_servers={bootstrap_servers}, group_id={group_id}\n")
    except:
        pass
    
    print(f"KafkaConsumer: creating consumer for topic {topic}, servers {bootstrap_servers}, group_id {group_id}")
    sys.stdout.flush()
    
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=group_id,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    
    try:
        with open(_log_file, "a") as f:
            f.write(f"KafkaConsumer created successfully\n")
            # Log partition info
            partitions = consumer.partitions_for_topic(topic)
            f.write(f"Topic partitions: {partitions}\n")
    except Exception as e:
        pass
    
    print("KafkaConsumer created, waiting for messages...")
    sys.stdout.flush()
    
    msg_count = 0
    for msg in consumer:
        msg_count += 1
        if msg_count == 1:
            print(f"First message received! partition={msg.partition}, offset={msg.offset}, key={msg.key}")
            sys.stdout.flush()
        if msg_count % 10 == 0:
            print(f"Consumed {msg_count} messages")
            sys.stdout.flush()
        try:
            handler(msg.value)
        except Exception as e:
            print(f"Handler error: {e}")
            sys.stdout.flush()


