#!/usr/bin/env bash
set -euo pipefail

# Comprehensive training and validation script for ML baselines and TGNN.
# Usage: bash ml/run_full_train.sh [output_dir]

OUT=${1:-./ml_artifacts}
mkdir -p "$OUT"

echo "=== Training ML Pipeline ==="

# 1. Train baseline models
echo "Training baseline models (AE, LSTM-AE)..."
#python -m /home/wini/zero-day/ml/src/ml_pipeline/train --out-dir "$OUT/baselines" --which ae --epochs 10
#python -m /home/wini/zero-day/ml/src/ml_pipeline.train --out-dir "$OUT/baselines" --which lstm --epochs 10
# train AE
$PYTHON - <<PY - "$OUT/baselines"
import sys
sys.argv = [sys.argv[0], "--out-dir", sys.argv[1], "--which", "ae", "--epochs", "10"]
from ml_pipeline import train
train.main()
PY

# train LSTM-AE
$PYTHON - <<PY - "$OUT/baselines"
import sys
sys.argv = [sys.argv[0], "--out-dir", sys.argv[1], "--which", "lstm", "--epochs", "10"]
from ml_pipeline import train
train.main()
PY


# 2. Generate synthetic graphs for TGNN (if needed)
echo "Generating synthetic graph data for TGNN..."
python -m graph_builder.synthetic_generator --out "$OUT/synthetic_events.jsonl" --count 2000
python -m graph_builder.main file --input-file "$OUT/synthetic_events.jsonl" --out-dir "$OUT/graphs" --window-size 60 --step 30

# 3. Train TGNN (if PyG available)
echo "Training TGNN..."
python << 'EOF'
import sys
try:
    from ml_pipeline.tgnn import train_tgnn
    train_tgnn(parquet_dir="./ml_artifacts/graphs", output_dir="./ml_artifacts/tgnn", epochs=5)
    print("TGNN training complete")
except ImportError:
    print("torch-geometric not installed, skipping TGNN")
    sys.exit(0)
EOF

# 4. Run validation suite
echo "Running validation suite (attack simulations)..."
python << 'EOF'
from ml_pipeline.validation import ValidationFramework

validator = ValidationFramework(pod_name="attack-target", namespace="dev")
metrics = validator.run_validation_suite()
report = validator.generate_report(metrics)
print(report)
validator.save_results("./ml_artifacts/validation_results.json")
EOF

echo "=== Training complete ==="
echo "Artifacts saved to: $OUT"
echo "  - baselines/autoencoder.pt: trained Autoencoder"
echo "  - baselines/lstm_ae.pt: trained LSTM-AE"
echo "  - tgnn/tgnn.pt: trained TGNN"
echo "  - graphs/: Parquet window outputs"
echo "  - validation_results.json: evaluation metrics"
