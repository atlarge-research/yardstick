from datetime import datetime
import os
import json
import re

EXP_DIR = os.environ['DIR_NAME']

server_logs = EXP_DIR+"/server/tshock/logs/"+os.listdir(EXP_DIR + '/server/tshock/logs')[0]

with open(server_logs, 'r') as f:
    lines = f.readlines()

bot_times = {}
for line in lines:
    if "Starting player work load" in line:
        first_bot_start_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        first_bot_start_time = first_bot_start_time.isoformat("T") + "Z"
        break
    
for line in lines:
    if "WORKLOAD COMPLETE" in line:
        first_bot_end_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        first_bot_end_time = first_bot_end_time.isoformat("T") + "Z"
        break

first_bot_join_time = None
for line in lines:
    if "has joined." in line:
        bot_name = re.search(r"Broadcast: (BOT_\w+)", line).group(1)
        bot_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        bot_time = bot_time.isoformat("T") + "Z"
        if first_bot_join_time is None:
            first_bot_join_time = bot_time
        bot_times[bot_name] = bot_time

# events throught the experiment
# first bot joins, first bot starts workloads, other bots joined, first bot ends workloads, ...
# we are interested from first bot joins to first bot ends workloads
with open(EXP_DIR + '/exp_times.json', 'w') as f:
    json.dump({"START_ANALYSIS": first_bot_join_time, "START_WORKLOAD": first_bot_start_time, "END_ANALYSIS": first_bot_end_time, "BOTS_JOINED": bot_times}, f)

