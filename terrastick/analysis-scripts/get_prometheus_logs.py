import os
import requests
import json
from datetime import datetime, timedelta

PROMETHEUS_SERVER = os.getenv("PROMETHEUS_IP")
PROMETHEUS_PORT = "9090"
PROMETHEUS_SCRAPE_INTERVAL = "5s"

metrics = {
    "node_cpu_utilization_raw": "node_cpu_seconds_total", # this is raw data, calculations done in analysis.py
    "node_cpu_utilization_custom": "avg%20without%20%28cpu%2C%20mode%29%20%281%20-%20rate%28node_cpu_seconds_total%7Bmode%3D%27idle%27%7D%5B1m%5D%29%29",
    "node_memory_utilization_custom": "1%20-%20%28%28avg_over_time%28node_memory_MemFree_bytes%5B10m%5D%29%20%2B%20avg_over_time%28node_memory_Cached_bytes%5B10m%5D%29%20%2B%20avg_over_time%28node_memory_Buffers_bytes%5B10m%5D%29%29%20%2F%20avg_over_time%28node_memory_MemTotal_bytes%5B10m%5D%29%29"
}

SAVE_DIR = os.path.join(os.getenv("DIR_NAME"), "prometheus/json_data")

os.makedirs(SAVE_DIR, exist_ok=True)

with open(os.path.join(os.getenv("DIR_NAME"), "exp_times.json"), 'r') as f:
    data = json.load(f)
    START_UTC = (datetime.strptime(data["START_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=2)).isoformat() + "Z"
    END_UTC = (datetime.strptime(data["END_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=2)).isoformat() + "Z"

for metric_name, metric in metrics.items():
    response = requests.get(f"http://{PROMETHEUS_SERVER}:{PROMETHEUS_PORT}/api/v1/query_range", params={"query": metric, "start": START_UTC, "end": END_UTC, "step": PROMETHEUS_SCRAPE_INTERVAL})
    if response.status_code == 200:
        response_data = response.json()
        # need to convert from UTC to CET
        for result in response_data['data']['result']:
            for value in result['values']:
                timestamp_utc = datetime.utcfromtimestamp(value[0])
                timestamp_cet = timestamp_utc + timedelta(hours=2)
                value[0] = timestamp_cet.timestamp()
        with open(os.path.join(SAVE_DIR, f"{metric_name}.json"), 'w') as f:
            json.dump(response_data, f)
    else:
        print(f"Failed to retrieve {metric_name}")
        print("due to this reason-",response)

