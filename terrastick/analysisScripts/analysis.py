import seaborn as sns
import matplotlib.pyplot as plt

file2= '2023-06-08.01.04.36_out.log'
with open(file2, 'r') as f:
    lines = f.readlines()

fifty_bot_lines = lines
fifty_bot_lines = [line for line in fifty_bot_lines if "GAME UPDATE TIME"  in line]



fifty_bot_times = [line.split(' ')[-1] for line in fifty_bot_lines]
fifty_bot_times = [line.split('\n')[0] for line in fifty_bot_times]

sns.boxplot(fifty_bot_times)
plt.title('3 Bot DAS5 Response Times')
plt.show()