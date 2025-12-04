Jury Presentation Guide
=======================

Use this short guide to present the PoC to the jury (5–10 minute flow).

1) One-slide summary (30s)
- Problem: detect zero-day lateral movement from flow events.
- Approach: streaming graph builder → temporal GNN inference → XAI explanations → containment operator.

2) Live demo flow (3–4 minutes)
- Show `kubectl get pods -n ml` to prove services are running.
- Run `bash scripts/demo_full.sh` to generate attack events and show results (this script runs the file-mode PoC and copies XAI output into the inference pod).
- Open `kubectl -n ml exec -it <inference-pod> -- cat /data/processed/latest_nodes.parquet.xai.json` to show top anomalous nodes and feature-based explanations.

3) Architecture slide (30s)
- Components: Producers → Kafka (bootstrap) → `graph-builder` (windows/parquet) → `inference-watcher` → XAI sidecar / `containment` operator (to be implemented).

4) Q&A and limitations (1-2 minutes)
- Mention that Minikube is single-node and we used a synthetic fallback for deterministic demos; production uses Strimzi/Redpanda/KRaft cluster.
- Note the TGNN and operator are skeletons included for future work.

5) Artefacts for reviewers
- Point them to `report/` for the DOCX deliverables and `report/REPRODUCE.md` for exact commands.
