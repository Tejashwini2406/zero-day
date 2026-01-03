#!/usr/bin/env bash
set -euo pipefail
# Safe cleanup: removes Python cache/build artifacts and archives large binaries
HERE=$(cd "$(dirname "$0")" && pwd)/..
ARCHIVE_DIR="$HERE/archive_cleanup"
mkdir -p "$ARCHIVE_DIR"

echo "Cleaning __pycache__ directories and .pyc files..."
find "$HERE" -type d -name "__pycache__" -print0 | xargs -0 -r rm -rf
find "$HERE" -type f -name "*.pyc" -print0 | xargs -0 -r rm -f

echo "Removing *.egg-info directories..."
find "$HERE" -maxdepth 3 -type d -name "*.egg-info" -print0 | xargs -0 -r rm -rf

echo "Removing backup files (*.bak, *~) in repo..."
find "$HERE" -type f \( -name "*.bak" -o -name "*~" \) -print0 | xargs -0 -r rm -f

echo "Archiving large files (>50MB) to $ARCHIVE_DIR..."
find "$HERE" -type f -size +50M -print0 | while IFS= read -r -d '' f; do
  bn=$(basename "$f")
  dest="$ARCHIVE_DIR/$bn"
  if [ -e "$dest" ]; then
    dest="$ARCHIVE_DIR/${bn}.$(date +%s%N)"
  fi
  echo "Archiving: $f -> $dest"
  if ! mv -- "$f" "$dest"; then
    echo "Warning: failed to move $f; skipping"
    continue
  fi
done

echo "Listing archived items:" 
ls -lh "$ARCHIVE_DIR" || true
echo "Cleanup complete. Review $ARCHIVE_DIR before permanently deleting archived files."

exit 0
