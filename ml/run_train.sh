#!/usr/bin/env bash
set -euo pipefail

OUT=${1:-./models}
mkdir -p "$OUT"
python -m ml_pipeline.train --out-dir "$OUT" --which ae --epochs 5
python -m ml_pipeline.train --out-dir "$OUT" --which lstm --epochs 5

echo "Models saved to $OUT"
