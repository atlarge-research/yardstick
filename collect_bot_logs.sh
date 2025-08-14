#!/bin/bash

# Script to manually collect bot logs from nodes
# Usage: ./collect_bot_logs.sh [output_directory]

OUTPUT_DIR="${1:-./bot_logs_$(date +%Y%m%d_%H%M%S)}"
NODES="node031 node032"

echo "Collecting bot logs to: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

for node in $NODES; do
    echo "Collecting logs from $node..."
    
    # Create directory for this node
    mkdir -p "$OUTPUT_DIR/${node}"
    
    # Copy all walkbot logs from /tmp on the node
    rsync -av "aco237@${node}:/tmp/walkbot_*_${node}.log" "$OUTPUT_DIR/${node}/" 2>/dev/null || {
        echo "  No logs found on $node (or connection failed)"
        continue
    }
    
    # Count and list the logs
    log_count=$(ls "$OUTPUT_DIR/${node}"/walkbot_*.log 2>/dev/null | wc -l)
    echo "  Collected $log_count log files from $node"
    
    if [ $log_count -gt 0 ]; then
        echo "  Log files:"
        ls -la "$OUTPUT_DIR/${node}"/walkbot_*.log
    fi
done

echo "Bot log collection complete. Files saved to: $OUTPUT_DIR"
echo "To view a specific bot log: cat $OUTPUT_DIR/node031/walkbot_001_node031.log"
