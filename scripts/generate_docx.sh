#!/usr/bin/env bash
# Convert a markdown file to DOCX using pandoc.
# Usage: ./scripts/generate_docx.sh input.md "output.docx"

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 input.md \"output.docx\""
  exit 1
fi

INPUT="$1"
OUTPUT="$2"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "pandoc not installed. Install pandoc to enable conversion."
  exit 2
fi

pandoc "$INPUT" -o "$OUTPUT"
echo "Generated $OUTPUT"
