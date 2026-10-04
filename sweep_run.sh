#!/usr/bin/env bash
# Usage: sweep_run.sh <label> <n_requests>   (fires 512-token payload; wall-time only)
LABEL=$1
N=$2
PAYLOAD=N:/Strata/bench-payload-200k-512.json
for i in $(seq 1 "$N"); do
  t0=$(date +%s.%N)
  curl -s -m 1800 -H "Content-Type: application/json" \
    --data-binary @"$PAYLOAD" \
    http://127.0.0.1:8080/v1/chat/completions -o /dev/null -w "req$i total=%{time_total}s\n" || echo "req$i FAILED"
  echo "$LABEL req$i wall=$(echo "$(date +%s.%N) - $t0" | bc)"
  sleep 2
done
