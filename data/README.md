Data folder with small representative samples for each dataset listed in DATASETS.md.

These are placeholder/example files so the pipeline can be exercised locally without downloading large external datasets.

Structure:
- kubernetes_anomaly/events.jsonl        : pod metrics / network flow events (sample)
- kubeiq/events.jsonl                    : KubeiQ-style generated anomalies (sample)
- nslkdd/nslkdd_sample.csv               : adapted NSL-KDD CSV sample (mapped to flow fields)
- opentelemetry_ebpf/sample_syscalls.jsonl : eBPF-style syscall traces (sample)
- cloud_vulns/cloud_vulns_sample.csv     : small cloud vulnerability records
- graph_anomaly/sample_graph_events.jsonl: temporal graph event sample

To replace with real datasets, download into `data/<dataset>/` and update `scripts/download_datasets.sh` with credentials/URLs.
