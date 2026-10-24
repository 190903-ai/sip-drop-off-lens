#!/usr/bin/env bash
# Rerun a resumable pipeline step until it reports no work left. Survives provider outages
# (e.g. Gemma 503 "service unavailable"): failed batches are simply picked up on the next pass.
# Usage: bash pipeline/run_until_done.sh pipeline/detect_stories.py data/detect_log.txt
cd "$(dirname "$0")/.."
script="$1"; log="$2"
for pass in $(seq 1 200); do
  echo "=== pass $pass $(date '+%H:%M') ===" >> "$log"
  ./.venv/Scripts/python.exe -u "$script" >> "$log" 2>&1
  if grep -q " 0 to go" <(tail -n 20 "$log"); then
    echo "=== all done $(date '+%H:%M') ===" >> "$log"
    exit 0
  fi
  sleep 300  # provider likely overloaded; wait 5 minutes before the next pass
done
