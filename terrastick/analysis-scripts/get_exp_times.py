from datetime import datetime
import os
import requests

EXP_DIR = os.environ['DIR_NAME']

server_logs = EXP_DIR+"/server/tshock/logs/"+os.listdir(EXP_DIR + '/server/tshock/logs')[0]


with open(server_logs, 'r') as f:
    lines = f.readlines()

start_time = None
end_time = None
for line in lines:
    if "Starting player work load" in line:
        start_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        break
    
for line in lines:
    if "WORKLOAD COMPLETE" in line:
        end_time = datetime.strptime(' '.join(line.split(' ')[:2]), '%Y-%m-%d %H:%M:%S')
        break


with open(EXP_DIR + '/exp_times.txt', 'w') as f:
    f.write('START={}\n'.format(start_time))
    f.write('END={}\n'.format(end_time))

