#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)/..
echo "Starting normal demo..."

if [ -f "$HERE/scripts/produce_events.py" ]; then
  echo "Running produce_events.py for normal traffic (press Ctrl+C to stop)"
  python3 "$HERE/scripts/produce_events.py" || echo "produce_events.py exited"
else
  echo "Warning: produce_events.py not found in scripts/. Please adapt this script to your producer."
fi

echo "Normal demo complete."

exit 0
