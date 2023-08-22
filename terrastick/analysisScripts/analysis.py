import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import os

EXP_DIR = os.environ['DIR_NAME']

plots_dir = EXP_DIR + '/plots'

# Ensure the plots directory exists
if not os.path.exists(plots_dir):
    os.makedirs(plots_dir)

ServerLogs = EXP_DIR+"/server/tshock/logs/"+os.listdir(EXP_DIR + '/server/tshock/logs')[0]
PacketLogs = EXP_DIR+"/server/tshock/PacketLogs/"+os.listdir(EXP_DIR + '/server/tshock/PacketLogs')[0]

# Extract start and end times from server logs
with open(ServerLogs, 'r') as f:
    lines = f.readlines()
    
for line in lines:
    if "start" in line:
        start_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
    if "WORKLOAD COMPLETE" in line:
        end_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')

# Extract game update times from packet logs within the start and end times
with open(PacketLogs, 'r') as f:
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
