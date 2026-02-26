#!/bin/bash
# VECINITA-RIOS: Isolation Wrapper
# Path: tests/query_isolation.sh

CONTAINER_NAME="vecinita-app"

echo "--- Injecting probe into $CONTAINER_NAME ---"

# Ensure tests dir exists in container
docker exec $CONTAINER_NAME mkdir -p /app/tests

# Copy the probe from the local tests folder to the container tests folder
docker cp tests/query_isolation.py $CONTAINER_NAME:/app/tests/

# Run the probe
docker exec $CONTAINER_NAME python3 /app/tests/query_isolation.py "$@"

if [ $? -eq 0 ]; then
    echo "--- PROBE PASSED ---"
else
    echo "--- PROBE FAILED ---"
fi
