import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import json
import os

exp_dir = os.environ['DIR_NAME']
prometheus_json_dir = exp_dir + '/prometheus/json_data'
plots_dir = exp_dir + '/plots'

# Ensure the plots directory exists
if not os.path.exists(plots_dir):
    os.makedirs(plots_dir)

server_logs = exp_dir+"/server/tshock/logs/"+os.listdir(exp_dir + '/server/tshock/logs')[0]
packet_logs = exp_dir+"/server/tshock/PacketLogs/"+os.listdir(exp_dir + '/server/tshock/PacketLogs')[0]

total_memory_bytes_quantity = None
number_of_cores_quantity = None
number_of_processes_in_group_quantity = None
cpu_utilization_percent_json = None
disk_reads_bytes_json = None
disk_writes_bytes_json = None
memory_utilization_bytes_json = None
number_of_threads_by_thread_group_name_json = None
thread_states_json = None
total_number_of_threads_json = None

# Load the json files and extract the quantities/json data
with open(prometheus_json_dir + '/total_memory_bytes.json', 'r') as f:
    total_memory_bytes_quantity = json.load(f)['quantity']
with open(prometheus_json_dir + '/number_of_cores.json', 'r') as f:
    number_of_cores_quantity = json.load(f)['quantity']
with open(prometheus_json_dir + '/number_of_processes_in_group.json', 'r') as f:
    number_of_processes_in_group_quantity = json.load(f)['quantity']
with open(prometheus_json_dir + '/cpu_utilization_percent.json', 'r') as f:
    cpu_utilization_percent_json = json.load(f)
with open(prometheus_json_dir + '/disk_reads_bytes.json', 'r') as f:
    disk_reads_bytes_json = json.load(f)
with open(prometheus_json_dir + '/disk_writes_bytes.json', 'r') as f:
    disk_writes_bytes_json = json.load(f)
with open(prometheus_json_dir + '/memory_utilization_bytes.json', 'r') as f:
    memory_utilization_bytes_json = json.load(f)
with open(prometheus_json_dir + '/number_of_threads_by_thread_group_name.json', 'r') as f:
    number_of_threads_by_thread_group_name_json = json.load(f)
with open(prometheus_json_dir + '/thread_states.json', 'r') as f:
    thread_states_json = json.load(f)
with open(prometheus_json_dir + '/total_number_of_threads.json', 'r') as f:
    total_number_of_threads_json = json.load(f)

start_time=None
end_time=None
bot_join_times=[]
# all of these times are in CET
with open(exp_dir + '/exp_times.json', 'r') as f:
    data = json.load(f)
    start_time = start_time = datetime.strptime(data["START_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ")
    end_time = end_time = datetime.strptime(data["END_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ")
    bot_join_times = [datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ") for time in data["BOTS_JOINED"].values()]


# this is required for prometheus graphs whose timings are in unix format
# Convert the provided timestamps to UNIX format
def convert_to_unix(timestamp):
    return int(datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").timestamp())
experiment_timings = None
with open(exp_dir + '/exp_times.json', 'r') as f:
    experiment_timings = json.load(f)
# Convert all timestamps
experiment_unix_times = {key: convert_to_unix(val) for key, val in experiment_timings.items() if key != "BOTS_JOINED"}
bots_unix_times = {key: convert_to_unix(val) for key, val in experiment_timings["BOTS_JOINED"].items()}
# Calculate time elapsed from the "START_ANALYSIS" event
start_analysis_time = experiment_unix_times["START_ANALYSIS"]
start_workload_elapsed = experiment_unix_times["START_WORKLOAD"] - start_analysis_time
bots_elapsed_times = {key: val - start_analysis_time for key, val in bots_unix_times.items()}



# Extract game update times from packet logs within the start and end times
with open(packet_logs, 'r') as f: 
    lines = f.readlines()
game_update_lines = [line for line in lines if "GAME UPDATE TIME" in line and start_time <= datetime.strptime(':'.join(line.split(':')[0:3]).strip(), '%m/%d/%Y %I:%M:%S %p') <= end_time]

# Extract timestamps and response times
update_time_timestamps = [datetime.strptime(':'.join(line.split(':')[0:3]).strip(), '%m/%d/%Y %I:%M:%S %p') for line in game_update_lines]
game_update_times = [float(line.split(' ')[-1]) for line in game_update_lines]

# Plot the response times
plt.figure(figsize=(20, 10))
plt.plot(update_time_timestamps, game_update_times, label='Response Time')

# Add red lines for bot join times
for bot_join_time in bot_join_times:
    plt.axvline(x=bot_join_time, color='r', linestyle='--', alpha=0.5, label='Bot Joined')

# To prevent duplicate labels in the legend, we'll handle them here:
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))

plt.legend(by_label.values(), by_label.keys())
plt.xlabel('Time')
plt.ylabel('Game Update Time (ms)')
plt.title('Game Update Times with Bot Join Times Highlighted')
plt.savefig(os.path.join(plots_dir, 'game_times_with_bot_joins.pdf'))

# Extract and plot packet distribution
corrected_packet_types = [line.split("[Recv]")[1].split('(')[1].split(')')[0] for line in lines if "[Recv]" in line]
filtered_packet_types = [packet for packet in corrected_packet_types if not any(char.isdigit() for char in packet)]
filtered_packet_counts = {packet: filtered_packet_types.count(packet) for packet in set(filtered_packet_types)}
sorted_filtered_packet_counts = dict(sorted(filtered_packet_counts.items(), key=lambda item: item[1], reverse=True))
top_filtered_packet_counts = list(sorted_filtered_packet_counts.items())[:20]
packet_names_filtered = [item[0] for item in top_filtered_packet_counts]
packet_counts_filtered = [item[1] for item in top_filtered_packet_counts]

plt.figure(figsize=(15, 10))
plt.bar(packet_names_filtered, packet_counts_filtered)
plt.xticks(rotation=90)
plt.xlabel('Packet Type')
plt.ylabel('Count')
plt.title('Corrected Distribution of Top 20 Packet Types Sent to the Server')
plt.tight_layout()
plt.savefig(os.path.join(plots_dir, 'packet_distribution.pdf'))

# Extract the time series data from provided data
timestamps, utilization_percent = zip(*cpu_utilization_percent_json['data']['result'][0]['values'])
timestamps = [int(ts) for ts in timestamps]
utilization_percent = [float(value) for value in utilization_percent]

timestamps_elapsed = [ts - start_analysis_time for ts in timestamps]
bots_elapsed_times = {key: val - start_analysis_time for key, val in bots_unix_times.items()}

# Plotting the graph with the adjustments
plt.figure(figsize=(15, 7))
plt.plot(timestamps_elapsed, utilization_percent, '-o', label='CPU Utilization (%)')

# Annotating "START_WORKLOAD"
plt.axvline(x=start_workload_elapsed, linestyle="--", color="blue", label="Start Workload")
plt.text(start_workload_elapsed, min(utilization_percent), "Start Workload", rotation=90, verticalalignment="bottom", color="blue")

# Annotating "BOTS_JOINED"
for _, elapsed_time in bots_elapsed_times.items():
    plt.axvline(x=elapsed_time, linestyle="--", color="green")

# Label for "Bots Joined" in the legend
plt.plot([], [], linestyle="--", color="green", label="Bot Joined")
plt.title("CPU Utilization Over Time")
plt.xlabel("Time Elapsed (seconds)")
plt.ylabel("CPU Utilization (%)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
plt.savefig(os.path.join(plots_dir, 'cpu_utilization.pdf'))

# Extract the time series data for memory utilization
memory_timestamps, memory_utilization_bytes = zip(*memory_utilization_bytes_json['data']['result'][0]['values'])
memory_timestamps = [int(ts) for ts in memory_timestamps]
memory_utilization_bytes = [float(value) for value in memory_utilization_bytes]
# Define the conversion factor from bytes to megabytes and convert memory utilization bytes to megabytes
bytes_to_megabytes = 1 / (2**20)
memory_utilization_megabytes = [value * bytes_to_megabytes for value in memory_utilization_bytes]

total_memory_bytes = float(total_memory_bytes_quantity)
total_memory_megabytes = total_memory_bytes * bytes_to_megabytes
# Calculate memory utilization as a percentage of total memory
memory_utilization_percentage = [(value / total_memory_bytes) * 100 for value in memory_utilization_bytes]
memory_timestamps_elapsed = [ts - start_analysis_time for ts in memory_timestamps]


# Plotting the graph with adaptive y-axis scaling
plt.figure(figsize=(15, 7))
plt.plot(memory_timestamps_elapsed, memory_utilization_percentage, '-o', label='Memory Utilization (%)', color="purple")

# Setting y-axis limits to be adaptive to the data
upper_limit = max(memory_utilization_percentage) + 5  # Buffer of 5% above max value
plt.ylim(0, upper_limit)

# Annotating "START_WORKLOAD"
plt.axvline(x=start_workload_elapsed, linestyle="--", color="blue", label="Start Workload")
plt.text(start_workload_elapsed, 0, "Start Workload", rotation=90, verticalalignment="bottom", color="blue")

# Annotating "BOTS_JOINED"
for _, elapsed_time in bots_elapsed_times.items():
    plt.axvline(x=elapsed_time, linestyle="--", color="green")

# Label for "Bots Joined" in the legend
plt.plot([], [], linestyle="--", color="green", label="Bot Joined")

plt.title("Memory Utilization Over Time")
plt.xlabel("Time Elapsed (seconds)")
plt.ylabel("Memory Utilization (%)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
plt.savefig(os.path.join(plots_dir, 'memory_utilization_percent.pdf'))

# Plotting the graph for total memory used
plt.figure(figsize=(15, 7))
plt.plot(memory_timestamps_elapsed, memory_utilization_megabytes, '-o', label=f'Total Memory Used (MB)', color="purple")
plt.axvline(x=start_workload_elapsed, linestyle="--", color="blue", label="Start Workload")
plt.text(start_workload_elapsed, 0, "Start Workload", rotation=90, verticalalignment="bottom", color="blue")
for _, elapsed_time in bots_elapsed_times.items():
    plt.axvline(x=elapsed_time, linestyle="--", color="green")
plt.plot([], [], linestyle="--", color="green", label="Bot Joined")
plt.title("Total Memory Used Over Time")
plt.xlabel("Time Elapsed (seconds)")
plt.ylabel("Memory (MB)")
plt.legend(title=f"Total Memory Available: {total_memory_megabytes:.2f} MB")
plt.grid(True)
plt.tight_layout()
plt.show()
plt.savefig(os.path.join(plots_dir, 'memory_utilization_megabytes.pdf'))

# Extract the time series data for total number of threads
threads_timestamps, total_threads = zip(*total_number_of_threads_json['data']['result'][0]['values'])
threads_timestamps = [int(ts) for ts in threads_timestamps]
total_threads = [float(value) for value in total_threads]
threads_timestamps_elapsed = [ts - start_analysis_time for ts in threads_timestamps]

# Plotting the graph for total number of threads over time
plt.figure(figsize=(15, 7))
plt.plot(threads_timestamps_elapsed, total_threads, '-o', label=f'Total Number of Threads', color="purple")
plt.axvline(x=start_workload_elapsed, linestyle="--", color="blue", label="Start Workload")
plt.text(start_workload_elapsed, min(total_threads), "Start Workload", rotation=90, verticalalignment="bottom", color="blue")
for _, elapsed_time in bots_elapsed_times.items():
    plt.axvline(x=elapsed_time, linestyle="--", color="green")
plt.plot([], [], linestyle="--", color="green", label="Bot Joined")
plt.title("Total Number of Threads Over Time")
plt.xlabel("Time Elapsed (seconds)")
plt.ylabel("Number of Threads")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
plt.savefig(os.path.join(plots_dir, 'total_number_of_threads.pdf'))

# Extract the thread names data
thread_names_data = {}
for result in number_of_threads_by_thread_group_name_json['data']['result']:
    thread_name = result['metric']['threadname']
    if thread_name not in thread_names_data:
        thread_names_data[thread_name] = {
            "timestamps": [],
            "threads": []
        }
    for value in result['values']:
        thread_names_data[thread_name]["timestamps"].append(value[0])
        thread_names_data[thread_name]["threads"].append(float(value[1]))

# Convert timestamps to elapsed time
for thread_name, thread_data in thread_names_data.items():
    thread_data["timestamps_elapsed"] = [float(t) - start_analysis_time for t in thread_data["timestamps"]]

# Extract constant thread counts (assuming values are constant if the first and last values are the same)
constant_thread_counts = {name: data["threads"][0] for name, data in thread_names_data.items() if data["threads"][0] == data["threads"][-1]}

# 1. Printing the Different Thread Group Names
thread_group_names = list(constant_thread_counts.keys())
print("Thread Group Names:")
for name in thread_group_names:
    print(name)

# 2. Pie Chart
# Define a vibrant color palette
vibrant_colors = ['#E63946', '#F1FAEE', '#A8DADC', '#457B9D', '#1D3557', '#F4A261', '#2A9D8F', '#E9C46A']

# Define explode values to slightly separate each segment
explode = [0.05] * len(constant_thread_counts)

# Plotting the enhanced pie chart
plt.figure(figsize=(12, 8))
plt.pie(constant_thread_counts.values(), 
        labels=constant_thread_counts.keys(), 
        colors=vibrant_colors, 
        autopct=lambda p: '{:.0f}'.format(p * sum(constant_thread_counts.values()) / 100), 
        startangle=140,
        explode=explode,
        shadow=True,
        wedgeprops=dict(width=0.5, edgecolor='w'))

plt.title("Thread Counts for Constant Thread Groups", fontsize=16)
plt.tight_layout()
plt.show()

# 3. Graph for ".NET ThreadPool"
# Extract data for ".NET ThreadPool"
net_threadpool_data = thread_names_data[".NET ThreadPool"]

# Plotting the graph for ".NET ThreadPool" over time
plt.figure(figsize=(15, 7))
plt.plot(net_threadpool_data["timestamps_elapsed"], net_threadpool_data["threads"], '-o', color="blue", label=".NET ThreadPool")
plt.axvline(x=start_workload_elapsed, linestyle="--", color="red", label="Start Workload")
plt.text(start_workload_elapsed, min(net_threadpool_data["threads"]), "Start Workload", rotation=90, verticalalignment="bottom", color="red")
for _, elapsed_time in bots_elapsed_times.items():
    plt.axvline(x=elapsed_time, linestyle="--", color="green")
plt.plot([], [], linestyle="--", color="green", label="Bot Joined")
plt.title(".NET ThreadPool Threads Over Time")
plt.xlabel("Time Elapsed (seconds)")
plt.ylabel("Number of Threads")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
plt.savefig(os.path.join(plots_dir, 'net_threadpool.pdf'))

# Extract time series data for disk reads
disk_reads_timestamps_all = []
disk_reads_values_all = []
for entry in disk_reads_bytes_json['data']['result']:
    for value in entry['values']:
        disk_reads_timestamps_all.append(value[0])
        disk_reads_values_all.append(float(value[1]))

# Extract time series data for disk writes
disk_writes_timestamps_all = []
disk_writes_values_all = []
for entry in disk_writes_bytes_json['data']['result']:
    for value in entry['values']:
        disk_writes_timestamps_all.append(value[0])
        disk_writes_values_all.append(float(value[1]))

# Convert timestamps to elapsed time
disk_reads_elapsed_times_all = [float(t) - start_analysis_time for t in disk_reads_timestamps_all]
disk_writes_elapsed_times_all = [float(t) - start_analysis_time for t in disk_writes_timestamps_all]

# Convert bytes to megabytes (MBs)
disk_reads_values_MB = [value / 2**20 for value in disk_reads_values_all]
disk_writes_values_MB = [value / 2**20 for value in disk_writes_values_all]

# Plotting Disk Reads over Time in MBs
plt.figure(figsize=(15, 7))
plt.plot(disk_reads_elapsed_times_all, disk_reads_values_MB, '-o', color="blue", label="Disk Reads")
plt.axvline(x=start_workload_elapsed, linestyle="--", color="red", label="Start Workload")
plt.text(start_workload_elapsed, min(disk_reads_values_MB), "Start Workload", rotation=90, verticalalignment="bottom", color="red")
for _, elapsed_time in bots_elapsed_times.items():
    plt.axvline(x=elapsed_time, linestyle="--", color="green")
plt.plot([], [], linestyle="--", color="green", label="Bot Joined")
plt.title("Disk Reads Over Time")
plt.xlabel("Time Elapsed (seconds)")
plt.ylabel("Megabytes Read")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
plt.savefig(os.path.join(plots_dir, 'disk_reads.pdf'))

# Plotting Disk Writes over Time in MBs
plt.figure(figsize=(15, 7))
plt.plot(disk_writes_elapsed_times_all, disk_writes_values_MB, '-o', color="orange", label="Disk Writes")
plt.axvline(x=start_workload_elapsed, linestyle="--", color="red", label="Start Workload")
plt.text(start_workload_elapsed, min(disk_writes_values_MB), "Start Workload", rotation=90, verticalalignment="bottom", color="red")
for _, elapsed_time in bots_elapsed_times.items():
    plt.axvline(x=elapsed_time, linestyle="--", color="green")
plt.plot([], [], linestyle="--", color="green", label="Bot Joined")
plt.title("Disk Writes Over Time")
plt.xlabel("Time Elapsed (seconds)")
plt.ylabel("Megabytes Written")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
plt.savefig(os.path.join(plots_dir, 'disk_reads_writes.pdf'))
