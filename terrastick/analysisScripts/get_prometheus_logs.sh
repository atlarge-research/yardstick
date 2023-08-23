#!/bin/bash

# Use the provided PROMETHEUS_IP environment variable
PROMETHEUS_SERVER="$PROMETHEUS_IP"
PROMETHEUS_PORT="9090"

# Define the metrics of interest
declare -A metrics
metrics["node_cpu_utilization_raw"]="node_cpu_seconds_total" # this is raw data, calculations done in analysis.py
metrics["node_average_cpu_utilization"]="100 * avg without (cpu, mode) (1 - rate(node_cpu_seconds_total{mode="idle"}[1m]))" # this calculates the average CPU utilization across all cores and modes barring idle
metrics["node_memory_utilization"]="100 * (1 - ((avg_over_time(node_memory_MemFree_bytes[10m]) + avg_over_time(node_memory_Cached_bytes[10m]) + avg_over_time(node_memory_Buffers_bytes[10m])) / avg_over_time(node_memory_MemTotal_bytes[10m])))"
# metrics["network_io_bytes_sent"]="node_network_transmit_bytes_total"
# metrics["network_io_bytes_received"]="node_network_receive_bytes_total"

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
