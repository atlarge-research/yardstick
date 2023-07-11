import seaborn as sns
import matplotlib.pyplot as plt
import os
from datetime import datetime

# read CURRENT_DIR environment variable
CURRENT_DIR = os.environ['CURRENT_DIR']

# read the onle file in CURRENT_DIR/server/tshock/logs
ServerLogs = CURRENT_DIR+"/server/tshock/logs/"+os.listdir(CURRENT_DIR + '/server/tshock/logs')[0]

# read the only file in CURRENT_DIR/server/tshock/PacketLogs
PacketLogs = CURRENT_DIR+"/server/tshock/PacketLogs/"+os.listdir(CURRENT_DIR + '/server/tshock/PacketLogs')[0]

# get output file as the argument
output_file = sys.argv[1]
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
l = game_update_lines[0]
# 7/10/2023 4:05:32 PM: GAME UPDATE TIME : 600\n
print(datetime.strptime(l.split(':')[0].strip()+':'+l.split(":")[1].strip()+":"+l.split(":")[2].strip(),"%m/%d/%Y %I:%M:%S %p"))
game_update_lines = [
    line for line in game_update_lines 
    if start_time < datetime.strptime(line.split(':')[0].strip() + ':' + line.split(':')[1].strip() +":"+ line.split(':')[2].strip(), '%m/%d/%Y %I:%M:%S %p')
                    < end_time
]

# plot the response times of the workload through time
game_update_times = [line.split(' ')[-1] for line in game_update_lines]


# get the time stamp of of the current game_update_lines
update_time_timestamps = [datetime.strptime(line.split(':')[0].strip() + ':' + line.split(':')[1].strip() +":"+ line.split(':')[2].strip(), '%m/%d/%Y %I:%M:%S %p') for line in game_update_lines]


# plot the response times of the workload through time
print(len(update_time_timestamps),len(game_update_times))
plt.plot(update_time_timestamps, game_update_times)
# plt.title('2 * 3 Bots Heap Tiling '+'DAS5 Response Times')

# read the experiment config from CURRENT_DIR/server/config,txt
with open(CURRENT_DIR + '/server/config.txt', 'r') as f:
    lines = f.readlines()
for line in lines:
    if line.__contains__('DIR_NAME'):
        numBots = line.split('=')[-1]
        numBots = numBots.split('\n')[0]
    if line.__contains__('NUM_NODES'):
        num_nodes = line.split('=')[-1]
        num_nodes = num_nodes.split('\n')[0]
    if line.__contains__('NUM_BOTS_PER_NODE'):
        num_bots_node = line.split('=')[-1]
        num_bots_node = num_bots_node.split('\n')[0]
    if line.__contains__('TERRASTICK_TILING'):
        tiling = line.split('=')[-1]
        tiling = tiling.split("\n")[0]
        if tiling =='':
            tiling = "TEST"


plt.title(str(num_nodes) + ' * ' + str(num_bots_node) + ' Bots ' + tiling + ' DAS5 Response Times')
plt.savefig(CURRENT_DIR + '/bot/yardstick-terrastick-test-v0.15/terrastick/analysisScripts/'+num_nodes+'_'+num_bots_node+'_'+tiling+'_Response_Times.pdf')
plt.savefig(output_file)

