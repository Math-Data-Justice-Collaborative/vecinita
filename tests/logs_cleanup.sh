#!/bin/bash
#tests/logs_cleaup.sh
# Target directories: Root and logs/
TARGET_DIRS=". ./logs"

echo "=== Cleaning up stale logs (Older than today) ==="

for dir in $TARGET_DIRS; do
    if [ -d "$dir" ]; then
        echo "Processing directory: $dir"
        # Find files ending in .log modified more than 1 day ago and delete them
        find "$dir" -maxdepth 1 -name "*.log" -mtime +0 -type f -delete -print
    fi
done

echo "=== Cleanup Complete ==="
