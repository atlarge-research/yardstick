from datetime import datetime
import os
import json
import re

EXP_DIR = os.environ['DIR_NAME']

server_logs = EXP_DIR+"/server/tshock/logs/"+os.listdir(EXP_DIR + '/server/tshock/logs')[0]

with open(server_logs, 'r') as f:
    lines = f.readlines()

def convert_to_datetime(time_str):
    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')

def time_to_duration(start, end):
    delta = end - start
    return delta.total_seconds()

# Initial time parsing
bot_times = {}

for line in lines:
    if "Starting player work load" in line:
        first_bot_start_time = convert_to_datetime(' '.join(line.split(' ')[:2]))
        break

for line in lines:
    if "WORKLOAD COMPLETE" in line:
        first_bot_end_time = convert_to_datetime(' '.join(line.split(' ')[:2]))
        break

first_bot_join_time = None
for line in lines:
    if "has joined." in line:
        bot_name = re.search(r"Broadcast: (BOT_\w+)", line).group(1)
        bot_time = convert_to_datetime(' '.join(line.split(' ')[:2]))
        if first_bot_join_time is None:
            first_bot_join_time = bot_time
        bot_times[bot_name] = bot_time

# Convert to durations
start_workload_duration = time_to_duration(first_bot_join_time, first_bot_start_time)
end_analysis_duration = time_to_duration(first_bot_join_time, first_bot_end_time)
bot_durations = {k: time_to_duration(first_bot_join_time, v) for k, v in bot_times.items()}

# Save to JSON
with open(EXP_DIR + '/exp_times_durations.json', 'w') as f:
    json.dump({"TIME_TO_START_ANALYSIS": 0, "TIME_TO_START_WORKLOAD": start_workload_duration, "TIME_TO_END_ANALYSIS": end_analysis_duration, "TIME_TO_BOTS_JOINED": bot_durations, "START_ANALYSIS": first_bot_join_time, "END_ANALYSIS": first_bot_end_time}, f)
