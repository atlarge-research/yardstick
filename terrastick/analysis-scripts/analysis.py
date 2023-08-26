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

# times are in CET
server_logs = EXP_DIR+"/server/tshock/logs/"+os.listdir(EXP_DIR + '/server/tshock/logs')[0]
packet_logs = EXP_DIR+"/server/tshock/PacketLogs/"+os.listdir(EXP_DIR + '/server/tshock/PacketLogs')[0]

start_time=None
end_time=None
bot_join_times=[]

# all of these times are in CET
with open(EXP_DIR + '/exp_times.json', 'r') as f:
    data = json.load(f)
    start_time = start_time = datetime.strptime(data["START_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ")
    end_time = end_time = datetime.strptime(data["END_ANALYSIS"], "%Y-%m-%dT%H:%M:%SZ")
    bot_join_times = [datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ") for time in data["BOTS_JOINED"].values()]

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

