import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os

EXP_DIR = os.environ['DIR_NAME']

plots_dir = EXP_DIR + '/plots'

# Ensure the plots directory exists
if not os.path.exists(plots_dir):
    os.makedirs(plots_dir)

server_logs = EXP_DIR+"/server/tshock/logs/"+os.listdir(EXP_DIR + '/server/tshock/logs')[0]
packet_logs = EXP_DIR+"/server/tshock/PacketLogs/"+os.listdir(EXP_DIR + '/server/tshock/PacketLogs')[0]
cpu_utilization_json = EXP_DIR+"/prometheus/cpu_utilization.json"


# Extract start and end times from server logs
with open(server_logs, 'r') as f:
    lines = f.readlines()
    
for line in lines:
    if "Starting player work load" in line:
        start_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        break

for line in lines:
    if "WORKLOAD COMPLETE" in line:
        end_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        break

# Extract game update times from packet logs within the start and end times
with open(packet_logs, 'r') as f:
    
    lines = f.readlines()

game_update_lines = [line for line in lines if "GAME UPDATE TIME" in line and start_time <= datetime.strptime(':'.join(line.split(':')[0:3]).strip(), '%m/%d/%Y %I:%M:%S %p') <= end_time]

# Extract timestamps and response times
update_time_timestamps = [datetime.strptime(':'.join(line.split(':')[0:3]).strip(), '%m/%d/%Y %I:%M:%S %p') for line in game_update_lines]
game_update_times = [float(line.split(' ')[-1]) for line in game_update_lines]

# Highlight when bots join
bot_join_times = [datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S') for line in lines if "Player has joined" in line and start_time <= datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S') <= end_time]

# Plot the response times
plt.figure(figsize=(20, 10))
plt.plot(update_time_timestamps, game_update_times, label='Response Time')

# Add red lines for bot join times
for bot_join_time in bot_join_times:
    plt.axvline(x=bot_join_time, color='r', linestyle='--', alpha=0.5, label='Bot Joined')

# To prevent duplicate labels in the legend, we'll handle them here:
handles, labels = plt.gca().get_legend_handles_labels()
new_labels, new_handles = [], []
for handle, label in zip(handles, labels):
    if label not in new_labels:
        new_labels.append(label)
        new_handles.append(handle)

plt.legend(new_handles, new_labels)
plt.xlabel('Time')
plt.ylabel('Response Time (ms)')
plt.title('Response Times with Bot Join Times Highlighted')
plt.savefig(os.path.join(plots_dir, 'response_times_with_bot_joins.pdf'))

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

# Load the data from the cpu_utilization.json file
with open(cpu_utilization_json, "r") as file:
    cpu_utilization_data = json.load(file)

# Extracting and aggregating CPU utilization data across all cores and modes (excluding idle)
cpu_timeseries = cpu_utilization_data["data"]["result"]
aggregated_cpu_utilization = {}

for series in cpu_timeseries:
    mode = series["metric"]["mode"]
    if mode != "idle":  # Exclude the idle mode
        timestamps, values = zip(*series["values"])
        for i, timestamp in enumerate(timestamps):
            if timestamp not in aggregated_cpu_utilization:
                aggregated_cpu_utilization[timestamp] = 0
            aggregated_cpu_utilization[timestamp] += float(values[i])

# Sorting the data by timestamp for plotting
sorted_timestamps, sorted_values = zip(*sorted(aggregated_cpu_utilization.items()))

# Plotting the aggregated CPU utilization
plt.figure(figsize=(15, 8))
plt.plot(sorted_timestamps, sorted_values, label="Overall CPU Utilization", color='red')
plt.title("Aggregated CPU Utilization Over Time")
plt.xlabel("Timestamp")
plt.ylabel("Aggregated CPU Seconds")
plt.legend()
plt.grid(True)
plt.show()
