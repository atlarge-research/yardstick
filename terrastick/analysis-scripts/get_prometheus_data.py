import os
import requests
import json
from datetime import datetime, timedelta
import time

PROMETHEUS_SERVER = os.getenv("PROMETHEUS_IP")
PROMETHEUS_PORT = "9090"
PROMETHEUS_SCRAPE_INTERVAL = "5s"

series_metrics = {
    # process-exporter metrics
    "cpu_utilization_percent": "sum(rate(namedprocess_namegroup_cpu_seconds_total%7Bmode%3D~%22user%7Csystem%22%2Cgroupname%3D%22tshock-server%22%7D%5B1m%5D))*100",
    "memory_utilization_bytes": "sum(namedprocess_namegroup_memory_bytes%7Bgroupname%3D%22tshock-server%22%2Cjob%3D%22process-exporter%22%2Cmemtype%3D~%22resident%7Cswapped%22%7D)",
    "total_number_of_threads": "namedprocess_namegroup_num_threads",
    "number_of_threads_by_thread_group_name": "namedprocess_namegroup_thread_count",
    "disk_writes_bytes": "namedprocess_namegroup_write_bytes_total",
    "disk_reads_bytes": "namedprocess_namegroup_read_bytes_total",
    "thread_states": "namedprocess_namegroup_states",
}

instant_metrics = {
    # node-exporter metrics
    "number_of_cores": "count%20without(cpu%2C%20mode)%20(node_cpu_seconds_total%7Bmode%3D%22idle%22%7D)", # we can use any mode here, I have used idle
    "total_memory_bytes": 'node_memory_MemTotal_bytes',
    # process-exporter metrics
    "number_of_processes_in_group": "namedprocess_namegroup_num_procs",
}

SAVE_DIR = os.path.join(os.getenv("DIR_NAME"), "prometheus/json_data")

os.makedirs(SAVE_DIR, exist_ok=True)

with open(os.path.join(os.getenv("DIR_NAME"), "exp_times_durations.json"), 'r') as f:
    data = json.load(f)
    START_UTC = datetime.strptime(data["START_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ")
    END_UTC = datetime.strptime(data["END_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ")
    # Check if daylight saving is on or off
    if time.localtime().tm_isdst:
        START_UTC = (START_UTC - timedelta(hours=2)).isoformat() + "Z"
        END_UTC = (END_UTC - timedelta(hours=2)).isoformat() + "Z"
    else:
        START_UTC = (START_UTC - timedelta(hours=1)).isoformat() + "Z"
        END_UTC = (END_UTC - timedelta(hours=1)).isoformat() + "Z"

for metric_name, metric in series_metrics.items():
    url = f"http://{PROMETHEUS_SERVER}:{PROMETHEUS_PORT}/api/v1/query_range"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = f"query={metric}&start={START_UTC}&end={END_UTC}&step={PROMETHEUS_SCRAPE_INTERVAL}"
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        response_data = response.json()
        
        # Convert timestamps to durations
        for datapoint in response_data['data']['result']:
            for idx, ts_value_pair in enumerate(datapoint['values']):
                timestamp = float(ts_value_pair[0])
                # add 3600 or 7200 to the start_timestamp if daylight saving is on or off respectively
                start_timestamp = datetime.strptime(START_UTC, "%Y-%m-%dT%H:%M:%SZ").timestamp() + (7200 if time.localtime().tm_isdst else 3600)
                duration_from_start = timestamp - start_timestamp
                datapoint['values'][idx][0] = duration_from_start
                
        with open(os.path.join(SAVE_DIR, f"{metric_name}.json"), 'w') as f:
            json.dump(response_data, f)
    else:
        print(f"Failed to retrieve {metric_name}")
        print("due to this reason-", response.reason)


for metric_name, metric in instant_metrics.items():
    url = f"http://{PROMETHEUS_SERVER}:{PROMETHEUS_PORT}/api/v1/query"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = f"query={metric}&time={START_UTC}"
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        response_data = response.json()
        with open(os.path.join(SAVE_DIR, f"{metric_name}.json"), 'w') as f:
            json.dump({"quantity": response_data['data']['result'][0]['value'][1]}, f)
    else:
        print(f"Failed to retrieve {metric_name}")
        print("due to this reason-", response.reason)
