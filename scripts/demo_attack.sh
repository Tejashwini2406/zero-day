#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)/..
echo "Starting attack demo..."

if [ -f "$HERE/scripts/generate_attack.py" ]; then
  echo "Running generate_attack.py to produce attack events (press Ctrl+C to stop)"
  python3 "$HERE/scripts/generate_attack.py" || echo "generate_attack.py exited"
else
  echo "Warning: generate_attack.py not found in scripts/. Please adapt this script to your attack generator."
fi

echo "Attack demo complete."

exit 0
