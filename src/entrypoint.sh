#!/bin/bash
set -e

# Use default interval if not set
: "${INTERVAL_SECONDS:=300}"

echo "Running main.py every $INTERVAL_SECONDS seconds..."

while true; do
    python /app/main.py
    echo "Sleeping for $INTERVAL_SECONDS seconds..."
    sleep "$INTERVAL_SECONDS"
done
