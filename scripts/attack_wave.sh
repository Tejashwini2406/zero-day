#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)/..
ATTACK_FILE="$HERE/attack_events.jsonl"

# Configuration
WAVE_SIZE=100          # Events per wave
NUM_WAVES=5            # Number of waves
WAVE_DELAY=2           # Seconds between waves
TIMESTAMP=$(date +%s)

echo "🚀 Starting Attack Wave Demo"
echo "Generating $((WAVE_SIZE * NUM_WAVES)) attack events in $NUM_WAVES waves..."
echo ""

for ((wave=1; wave<=NUM_WAVES; wave++)); do
    echo "⚡ Wave $wave/$NUM_WAVES: Generating $WAVE_SIZE events..."
    
    for ((i=1; i<=WAVE_SIZE; i++)); do
        EVENT=$(cat <<EOF
{
  "timestamp": $(($TIMESTAMP + ($wave-1)*$WAVE_DELAY + $i)),
  "event_type": "alert",
  "severity": "high",
  "attack_type": "anomaly",
  "message": "Suspicious pattern detected (wave $wave)",
  "confidence": $((70 + RANDOM % 30))
}
EOF
)
        echo "$EVENT" >> "$ATTACK_FILE"
    done
    
    echo "   ✓ $WAVE_SIZE events written"
    
    if [ $wave -lt $NUM_WAVES ]; then
        echo "   ⏱️  Waiting ${WAVE_DELAY}s before next wave..."
        sleep $WAVE_DELAY
    fi
done

TOTAL=$((WAVE_SIZE * NUM_WAVES))
echo ""
echo "✅ Attack Wave Complete!"
echo "   Total events: $TOTAL"
echo "   File: $ATTACK_FILE"
echo ""
echo "   http://localhost:3000/d/5d8f9ba0-97ab-4cde-9684-701660ef10e3/zero-day-demo-dashboard"
echo ""

