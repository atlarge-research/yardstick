#!/bin/bash

# Use the provided PROMETHEUS_IP environment variable
PROMETHEUS_SERVER="$PROMETHEUS_IP"
PROMETHEUS_PORT="9090"

# Define the metrics of interest
declare -A metrics
metrics["cpu_utilization"]="node_cpu_seconds_total"
metrics["memory_usage"]="node_memory_usage_bytes"
metrics["threads_total"]="node_threads"
metrics["network_io_bytes_sent"]="node_network_transmit_bytes_total"
metrics["network_io_bytes_received"]="node_network_receive_bytes_total"

# Create SAVE_DIR using DIR_NAME environment variable
SAVE_DIR="$DIR_NAME/prometheus"

# Make sure the directory exists
mkdir -p $SAVE_DIR

# Extract START and END timestamps from DIR_NAME/exp_times.txt
source $DIR_NAME/exp_times.txt

# Retrieve and save metrics
for metric_name in "${!metrics[@]}"; do
    metric=${metrics[$metric_name]}
    curl -g "http://$PROMETHEUS_SERVER:$PROMETHEUS_PORT/api/v1/query_range?query=$metric&start=$START&end=$END&step=15s" > "$SAVE_DIR/$metric_name.json" || echo "Failed to retrieve $metric_name"
done
