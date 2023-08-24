import os
import requests
import json
from datetime import datetime, timedelta

PROMETHEUS_SERVER = os.getenv("PROMETHEUS_IP")
PROMETHEUS_PORT = "9090"
PROMETHEUS_SCRAPE_INTERVAL = "5s"

metrics = {
    "node_cpu_utilization_raw": "node_cpu_seconds_total", # this is raw data, calculations done in analysis.py
    "node_cpu_utilization_custom": "100%20*%20avg%20without%20(cpu%2C%20mode)%20(%0A%20%201%20-%20rate(node_cpu_seconds_total%7Bmode%3D%22idle%22%7D%5B1m%5D)%0A)",
    "node_memory_utilization_custom": "100%20*%20(1%20-%20((avg_over_time(node_memory_MemFree_bytes%5B10m%5D)%20%2B%20avg_over_time(node_memory_Cached_bytes%5B10m%5D)%20%2B%20avg_over_time(node_memory_Buffers_bytes%5B10m%5D))%20%2F%20avg_over_time(node_memory_MemTotal_bytes%5B10m%5D)))"
}

SAVE_DIR = os.path.join(os.getenv("DIR_NAME"), "prometheus/json_data")

os.makedirs(SAVE_DIR, exist_ok=True)

with open(os.path.join(os.getenv("DIR_NAME"), "exp_times.json"), 'r') as f:
    data = json.load(f)
    START_UTC = (datetime.strptime(data["START_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=2)).isoformat() + "Z"
    END_UTC = (datetime.strptime(data["END_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=2)).isoformat() + "Z"

for metric_name, metric in metrics.items():
    url = f"http://{PROMETHEUS_SERVER}:{PROMETHEUS_PORT}/api/v1/query_range"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = f"query={metric}&start={START_UTC}&end={END_UTC}&step={PROMETHEUS_SCRAPE_INTERVAL}"
    response = requests.request("POST", url, headers=headers, data=payload)
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
        print("due to this reason-", response.reason)
