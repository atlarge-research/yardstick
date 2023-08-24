import os
import requests
import json

PROMETHEUS_SERVER = os.getenv("PROMETHEUS_IP")
PROMETHEUS_PORT = "9090"
PROMETHEUS_SCRAPE_INTERVAL = "5s"

metrics = {
    "node_cpu_utilization_raw": 'node_cpu_seconds_total', # this is raw data, calculations done in analysis.py
    "node_cpu_utilization_custom": '100%20*%20avg%20without%20(cpu%2C%20mode)%20(%0A%20%201%20-%20rate(node_cpu_seconds_total%7Bmode%3D%22idle%22%7D%5B1m%5D)%0A)',
    "node_memory_utilization_custom": '100%20*%20(1%20-%20((avg_over_time(node_memory_MemFree_bytes%5B10m%5D)%20%2B%20avg_over_time(node_memory_Cached_bytes%5B10m%5D)%20%2B%20avg_over_time(node_memory_Buffers_bytes%5B10m%5D))%20%2F%20avg_over_time(node_memory_MemTotal_bytes%5B10m%5D)))'
}

SAVE_DIR = os.path.join(os.getenv("DIR_NAME"), "prometheus/json_data")

os.makedirs(SAVE_DIR, exist_ok=True)

with open(os.path.join(os.getenv("DIR_NAME"), "exp_times.json"), 'r') as f:
    data = json.load(f)
    START = data["START"]
    END = data["END"]

for metric_name, metric in metrics.items():
    response = requests.get(f"http://{PROMETHEUS_SERVER}:{PROMETHEUS_PORT}/api/v1/query_range", params={"query": metric, "start": START, "end": END, "step": PROMETHEUS_SCRAPE_INTERVAL})
    if response.status_code == 200:
        with open(os.path.join(SAVE_DIR, f"{metric_name}.json"), 'w') as f:
            json.dump(response.json(), f)
    else:
        print(f"Failed to retrieve {metric_name}")
