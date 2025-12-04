"""Red-team attack playbooks: container escape, privilege escalation, lateral movement.

Each playbook simulates an attack and captures telemetry for validation.
"""

import subprocess
import json
import time
from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class AttackResult:
    """Result of an attack simulation."""
    attack_id: str
    name: str
    mitre_technique: str
    detected: bool
    detection_latency_s: float
    false_positive: bool
    timestamp: str


class ContainerEscapePlaybook:
    """T1610: Container escape - attempts to break out of container namespace."""

    def __init__(self, pod_name: str, namespace: str):
        self.pod_name = pod_name
        self.namespace = namespace

    def run(self) -> List[Dict]:
        """Simulate container escape attack."""
        events = []

        # Step 1: Detect docker socket (evidence collection)
        events.append({
            "timestamp": time.time(),
            "event_type": "file_access",
            "syscall": "open",
            "path": "/var/run/docker.sock",
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "high",
            "mitre_technique": "T1610",
        })

        # Step 2: Attempt privileged container spawn
        events.append({
            "timestamp": time.time() + 1,
            "event_type": "process_creation",
            "command": "docker run --privileged -it alpine /bin/sh",
            "parent_process": "sh",
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "critical",
            "mitre_technique": "T1610",
        })

        # Step 3: Capability escalation
        events.append({
            "timestamp": time.time() + 2,
            "event_type": "capability_change",
            "syscall": "capset",
            "capabilities_added": ["CAP_SYS_ADMIN", "CAP_NET_ADMIN"],
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "critical",
            "mitre_technique": "T1610",
        })

        return events


class PrivilegeEscalationPlaybook:
    """T1548/T1548.001: Privilege escalation - abuse setuid binaries or kernel exploits."""

    def __init__(self, pod_name: str, namespace: str):
        self.pod_name = pod_name
        self.namespace = namespace

    def run(self) -> List[Dict]:
        """Simulate privilege escalation."""
        events = []

        # Step 1: Suspicious setuid binary execution
        events.append({
            "timestamp": time.time(),
            "event_type": "process_creation",
            "command": "/tmp/exploit_binary",
            "uid": 1000,
            "expected_uid": 0,
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "critical",
            "mitre_technique": "T1548.001",
        })

        # Step 2: Capability request
        events.append({
            "timestamp": time.time() + 1,
            "event_type": "syscall",
            "syscall": "prctl",
            "args": "PR_SET_DUMPABLE",
            "uid": 1000,
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "high",
            "mitre_technique": "T1548.001",
        })

        # Step 3: Successful UID 0 process
        events.append({
            "timestamp": time.time() + 2,
            "event_type": "process_creation",
            "command": "/bin/bash",
            "uid": 0,
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "critical",
            "mitre_technique": "T1548.001",
        })

        return events


class LateralMovementPlaybook:
    """T1021: Lateral movement - RPC calls to adjacent services, credential theft."""

    def __init__(self, pod_name: str, namespace: str):
        self.pod_name = pod_name
        self.namespace = namespace

    def run(self) -> List[Dict]:
        """Simulate lateral movement."""
        events = []

        # Step 1: Service discovery (enumeration)
        events.append({
            "timestamp": time.time(),
            "event_type": "dns_query",
            "query": "*.default.svc.cluster.local",
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "medium",
            "mitre_technique": "T1021",
        })

        # Step 2: Connection to adjacent service
        events.append({
            "timestamp": time.time() + 1,
            "event_type": "network.flow",
            "src_pod": self.pod_name,
            "dst_pod": "sensitive-service",
            "dst_port": 8080,
            "protocol": "TCP",
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "high",
            "mitre_technique": "T1021",
        })

        # Step 3: Credential exfiltration via HTTP
        events.append({
            "timestamp": time.time() + 2,
            "event_type": "http_request",
            "method": "POST",
            "path": "/api/admin/credentials",
            "body_size": 5000,
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "critical",
            "mitre_technique": "T1021",
        })

        return events


class DataExfiltrationPlaybook:
    """T1041: Exfiltration over network - abnormal outbound traffic."""

    def __init__(self, pod_name: str, namespace: str):
        self.pod_name = pod_name
        self.namespace = namespace

    def run(self) -> List[Dict]:
        """Simulate data exfiltration."""
        events = []

        # Step 1: Sudden increase in outbound traffic
        events.append({
            "timestamp": time.time(),
            "event_type": "network.flow",
            "src_pod": self.pod_name,
            "dst_ip": "8.8.8.8",  # External IP
            "bytes": 500000,  # Large transfer
            "protocol": "TCP",
            "pod": self.pod_name,
            "namespace": self.namespace,
            "severity": "critical",
            "mitre_technique": "T1041",
        })

        # Step 2: Multiple connections to unknown IPs
        for i in range(5):
            events.append({
                "timestamp": time.time() + i + 1,
                "event_type": "network.flow",
                "src_pod": self.pod_name,
                "dst_ip": f"203.0.113.{i}",  # Example external IPs
                "bytes": 100000,
                "protocol": "TCP",
                "pod": self.pod_name,
                "namespace": self.namespace,
                "severity": "high",
                "mitre_technique": "T1041",
            })

        return events


class AttackSimulator:
    """Orchestrates attack playbooks and collects telemetry."""

    playbooks = {
        "container_escape": ContainerEscapePlaybook,
        "privilege_escalation": PrivilegeEscalationPlaybook,
        "lateral_movement": LateralMovementPlaybook,
        "data_exfiltration": DataExfiltrationPlaybook,
    }

    def __init__(self, pod_name: str, namespace: str):
        self.pod_name = pod_name
        self.namespace = namespace
        self.results = []

    def run_attack(self, attack_name: str) -> List[Dict]:
        """Run a specific attack and return telemetry events."""
        if attack_name not in self.playbooks:
            raise ValueError(f"Unknown attack: {attack_name}")

        playbook_class = self.playbooks[attack_name]
        playbook = playbook_class(self.pod_name, self.namespace)
        return playbook.run()

    def run_all_attacks(self) -> Dict[str, List[Dict]]:
        """Run all attacks and return collected telemetry."""
        all_events = {}
        for attack_name in self.playbooks.keys():
            events = self.run_attack(attack_name)
            all_events[attack_name] = events
        return all_events


def evaluate_detection(
    model_scores: Dict[str, float],
    attack_events: Dict[str, float],
    threshold: float = 0.7,
) -> AttackResult:
    """Evaluate if an attack was detected.

    Args:
        model_scores: anomaly scores from ML model
        attack_events: ground truth attack events with timestamps
        threshold: anomaly score threshold

    Returns:
        AttackResult with detection metrics
    """
    detected = any(score > threshold for score in model_scores.values())
    false_positive = detected and not attack_events
    detection_latency = 0.0  # Calculated from first alert timestamp

    return AttackResult(
        attack_id="sim-001",
        name="simulated_attack",
        mitre_technique="T1610",
        detected=detected,
        detection_latency_s=detection_latency,
        false_positive=false_positive,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
