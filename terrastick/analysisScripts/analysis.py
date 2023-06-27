import seaborn as sns
import matplotlib.pyplot as plt

file2= '/Users/abalaji/repos/yardstick/terrastick/analysisScripts/2023-06-23.12.06.02_out.log'
with open(file2, 'r') as f:
    lines = f.readlines()

# sget all the lines that contain the word "GAME UPDATE TIME" between the start and end of the workload

start_line = 23143
end_line = 57692

fifty_bot_lines = [line for line in lines[start_line:end_line] if "GAME UPDATE TIME"  in line]



fifty_bot_times = [line.split(' ')[-1] for line in fifty_bot_lines]
fifty_bot_times = [line.split('\n')[0] for line in fifty_bot_times]

sns.boxplot(fifty_bot_times)
plt.title('4 Bot DAS5 Response Times')
plt.show()