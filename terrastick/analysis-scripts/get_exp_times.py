from datetime import datetime
import os
import json
import re

EXP_DIR = os.environ['DIR_NAME']

server_logs = EXP_DIR+"/server/tshock/logs/"+os.listdir(EXP_DIR + '/server/tshock/logs')[0]

with open(server_logs, 'r') as f:
    lines = f.readlines()

start_time = None
end_time = None
bot_times = {}
for line in lines:
    if "Starting player work load" in line:
        start_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        start_time = start_time.isoformat("T") + "Z"
        break
    
for line in lines:
    if "WORKLOAD COMPLETE" in line:
        end_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        end_time = end_time.isoformat("T") + "Z"
        break

for line in lines:
    if "Broadcast: BOT_" in line:
        bot_name = re.search(r"Broadcast: (BOT_\w+)", line).group(1)
        bot_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        bot_time = bot_time.isoformat("T") + "Z"
        bot_times[bot_name] = bot_time

with open(EXP_DIR + '/exp_times.json', 'w') as f:
    json.dump({"START": start_time, "END": end_time, "BOTS": bot_times}, f)

