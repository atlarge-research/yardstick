import seaborn as sns
import matplotlib.pyplot as plt
import os
from datetime import datetime

# read CURRENT_DIR environment variable
CURRENT_DIR = os.environ['CURRENT_DIR']

# read the onle file in CURRENT_DIR/server/tshock/logs
ServerLogs = os.listdir(CURRENT_DIR + '/server/tshock/logs')[0]

# read the only file in CURRENT_DIR/server/tshock/PacketLogs
PacketLogs = os.listdir(CURRENT_DIR + '/server/tshock/PacketLogs')[0]

with open(ServerLogs, 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "start" in line:
        start_line = line
    if "WORKLOAD COMPLETE" in line:
        end_line = line

# extract time stamp from start_line and end_line
start_time = start_line.split(' ')[0] + ' ' + start_line.split(' ')[1]
start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')

end_time = end_line.split(' ')[0] + ' ' + end_line.split(' ')[1]
end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

# get all the log lines between the start and end of the workload from PacketLogs
with open(PacketLogs, 'r') as f:
    lines = f.readlines()

# get all the lines that contain the word "GAME UPDATE TIME" between the start and end of the workload
game_update_lines = [line for line in lines if "GAME UPDATE TIME"  in line]
# filter all the lines between the start and end of the workload

game_update_lines = [line for line in game_update_lines if start_time < datetime.strptime(line.split(' ')[0] + ' ' + line.split(' ')[1], '%Y-%m-%d %H:%M:%S') < end_time]

# plot the response times of the workload through time
game_update_times = [line.split(' ')[-1] for line in game_update_lines]



# get the time stamp of of the current game_update_lines
update_time_timestamps = [datetime.strptime(line.split(' ')[0] + ' ' + line.split(' ')[1], '%Y-%m-%d %H:%M:%S') for line in game_update_lines]


# plot the response times of the workload through time
sns.lineplot(x=update_time_timestamps, y=game_update_times)
# plt.title('2 * 3 Bots Heap Tiling '+'DAS5 Response Times')


# read the experiment config from CURRENT_DIR/server/config,txt
with open(CURRENT_DIR + '/server/config.txt', 'r') as f:
    lines = f.readlines()
for line in lines:
    if line.__contains__('DIR_NAME'):
        numBots = int(line.split('=')[-1])
    if line.__contains__('NUM_NODES'):
        num_nodes = int(line.split('=')[-1])
    if line.__contains__('NUM_BOTS_PER_NODE'):
        num_bots_node = int(line.split('=')[-1])
    if line.__contains__('TERRASTICK_TILING'):
        tiling = line.split('=')[-1]


plt.title(str(num_nodes) + ' * ' + str(num_bots_node) + ' Bots ' + tiling + ' DAS5 Response Times')
plt.savefig(CURRENT_DIR + '/analysisScripts/'+num_nodes+'_'+num_bots_node+'_'+tiling+'_Response_Times.pdf')


