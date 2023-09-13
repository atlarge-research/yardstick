import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import json
import os

# Define paths
exp_dir = os.environ['DIR_NAME']
prometheus_json_dir = f'{exp_dir}/prometheus/json_data'
plots_dir = f'{exp_dir}/plots'

# Ensure plots directory exists
if not os.path.exists(plots_dir):
    os.makedirs(plots_dir)

# Load quantities and JSON data
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

prometheus_files = [
    'total_memory_bytes', 'number_of_cores', 'number_of_processes_in_group',
    'cpu_utilization_percent', 'disk_reads_bytes', 'disk_writes_bytes',
    'memory_utilization_bytes', 'number_of_threads_by_thread_group_name',
    'thread_states', 'total_number_of_threads'
]

data_dict = {key: load_json(f'{prometheus_json_dir}/{key}.json') for key in prometheus_files}

# Load experiment timings with durations
with open(f'{exp_dir}/exp_times_durations.json', 'r') as f:
    exp_timings = json.load(f)

# Time to start analysis is the base time
start_analysis_duration = exp_timings["TIME_TO_START_ANALYSIS"]

# Convert to time elapsed from start_analysis
def convert_to_elapsed(duration):
    return duration - start_analysis_duration

# Extract durations and convert to time elapsed from start_analysis
start_workload_elapsed = convert_to_elapsed(exp_timings["TIME_TO_START_WORKLOAD"])
end_analysis_elapsed = convert_to_elapsed(exp_timings["TIME_TO_END_ANALYSIS"])
bots_elapsed_times = {key: convert_to_elapsed(val) for key, val in exp_timings["TIME_TO_BOTS_JOINED"].items()}

# ... (rest of your code remains the same)

# Update CPU Utilization Plot
timestamps, utilization_percent = zip(*data_dict['cpu_utilization_percent']['data']['result'][0]['values'])
timestamps_elapsed = [convert_to_elapsed(ts) for ts in timestamps]
utilization_percent = [float(value) for value in utilization_percent]

# Plotting CPU Utilization, now using durations
plt.figure(figsize=(15, 7))
plt.plot(timestamps_elapsed, utilization_percent, '-o', label='CPU Utilization (%)')

# Annotate "START_WORKLOAD"
plt.axvline(x=start_workload_elapsed, linestyle="--", color="blue", label="Start Workload")
plt.text(start_workload_elapsed, min(utilization_percent), "Start Workload", rotation=90, verticalalignment="bottom", color="blue")

# Annotate "BOTS_JOINED"
for _, elapsed_time in bots_elapsed_times.items():
    plt.axvline(x=elapsed_time, linestyle="--", color="green")

# Legend for "Bots Joined"
plt.plot([], [], linestyle="--", color="green", label="Bot Joined")
plt.title("CPU Utilization Over Time")
plt.xlabel("Time Elapsed (seconds)")
plt.ylabel("CPU Utilization (%)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
plt.savefig(f'{plots_dir}/cpu_utilization.pdf')
