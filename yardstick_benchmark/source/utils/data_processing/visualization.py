import pandas as pd
import seaborn as sns
from pathlib import Path
import os

sns.set_palette("deep")

def create_plots_directory():
    try:
        os.mkdir("./plots")
    except OSError as error:
        pass

def plot_box_cpu(path, output_file_name):
    data = pd.read_csv(path, names = ["timestamp","measurement","core_id","cpu","host","physical_id","time_active","time_guest","time_guest_nice","time_idle","time_iowait","time_irq","time_nice","time_softirq","time_steal","time_system","time_user"])
    data["timestamp"] = data["timestamp"].transform(lambda x: x - x.min())
    data["timestamp_m"] = data["timestamp"] / 60
    data[data.cpu == "cpu_total"]
    data["time_total"] = data.time_active + data.time_idle
    data["util"] = 100 * data.time_active / data.time_total
    data = data[data.groupby(["timestamp", "cpu"])["time_total"].rank(ascending=False) <= 1]
    data.head()

    custom_params = {"axes.spines.right": False, "axes.spines.top": False, "axes.spines.left": False}
    sns.set_theme(style="whitegrid", rc=custom_params)

    cpu_box = sns.boxplot(x=data["util"], width=.3, fill=False)
    cpu_box.set_xlabel("CPU Usage [%]")

    create_plots_directory()
    
    cpu_box.figure.set_figheight(3)
    cpu_box.get_figure().savefig(f"./plots/{output_file_name}.png")
    cpu_box.get_figure().clf()

# def plot_line_cpu(path, output_file_name):
#     data = pd.read_csv(path, names = ["timestamp","measurement","core_id","cpu","host","physical_id","time_active","time_guest","time_guest_nice","time_idle","time_iowait","time_irq","time_nice","time_softirq","time_steal","time_system","time_user"])
#     data["timestamp"] = data["timestamp"].transform(lambda x: x - x.min())
#     data["timestamp_m"] = data["timestamp"] / 60
#     data[data.cpu == "cpu_total"]
#     data["time_total"] = data.time_active + data.time_idle
#     data["util"] = 100 * data.time_active / data.time_total
#     data = data[data.groupby(["timestamp", "cpu"])["time_total"].rank(ascending=False) <= 1]
#     data.head()

#     custom_params = {"axes.spines.right": False, "axes.spines.top": False}
#     sns.set_theme(style="ticks", rc=custom_params)
#     cpu_line = sns.lineplot(data, x="timestamp_m", y="util")
#     cpu_line.grid(axis="y")
#     cpu_line.set_ylim(bottom=0)
#     cpu_line.set_ylabel("CPU utilization [%]")
#     cpu_line.set_xlabel("Time [m]")

#     create_plots_directory()
    
#     cpu_line.get_figure().savefig(f"./plots/{output_file_name}.png")
#     cpu_line.get_figure().clf()

# def plot_line_tick_duration(path, output_file_name):
#     data = pd.read_csv(path, names = ["timestamp", "label", "node", "jolokia_endpoint", "tick_duration_ms"])
#     data["timestamp"] = data["timestamp"].transform(lambda x: x - x.min())
#     data["timestamp_m"] = data["timestamp"] / 60
#     data.head()

#     custom_params = {"axes.spines.right": False, "axes.spines.top": False}
#     sns.set_theme(style="ticks", rc=custom_params)
#     tick_line = sns.lineplot(data, x="timestamp_m", y="tick_duration_ms")
#     tick_line.grid(axis="y")
#     tick_line.set_ylim(bottom=0)
#     tick_line.set_ylabel("Tick duration [ms]")
#     tick_line.set_xlabel("Time [m]")

#     create_plots_directory()

#     tick_line.get_figure().savefig(f"./plots/{output_file_name}.png")
#     tick_line.get_figure().clf()

def plot_box_tick_duration(path, output_file_name):
    data = pd.read_csv(path, names = ["timestamp", "label", "node", "jolokia_endpoint", "tick_duration_ms"])
    data.head()

    custom_params = {"axes.spines.right": False, "axes.spines.top": False, "axes.spines.left": False}
    sns.set_theme(style="whitegrid", rc=custom_params)
    tick_box = sns.boxplot(x=data["tick_duration_ms"], width=.3, fill=False, flierprops={"marker": "."})
    tick_box.set_xlabel("Tick Duration [ms]")

    create_plots_directory()

    tick_box.get_figure().savefig(f"./plots/{output_file_name}.png")
    tick_box.get_figure().clf()

def plot_box_memory(path, output_file_name):
    data = pd.read_csv(path, names=["timestamp", "label", "node"])

# def plot_violin_tick_duration(path, output_file_name):
#     data = pd.read_csv(path, names = ["timestamp", "label", "node", "jolokia_endpoint", "tick_duration_ms"])
#     data.head()

#     custom_params = {"axes.spines.right": False, "axes.spines.top": False}
#     sns.set_theme(style="ticks", rc=custom_params)
#     tick_violin = sns.violinplot(x=data["tick_durhttps://www.influxdata.com/time-series-platform/telegraf/ation_ms"])
#     tick_violin.set_xlabel("Tick Duration [ms]")

#     create_plots_directory()

#     tick_violin.get_figure().savefig(f"./plots/{output_file_name}.png")
#     tick_violin.get_figure().clf()

# def plot_kde_tick_duration(path, output_file_name):
#     data = pd.read_csv(path, names = ["timestamp", "label", "node", "jolokia_endpoint", "tick_duration_ms"])
#     data.head()

#     custom_params = {"axes.spines.right": False, "axes.spines.top": False}
#     sns.set_theme(style="ticks", rc=custom_params)
#     tick_kde = sns.kdeplot(x=data["tick_duration_ms"], cut=0)
#     tick_kde.set_xlabel("Tick Duration [ms]")


#     create_plots_directory()

#     tick_kde.get_figure().savefig(f"./plots/{output_file_name}.png")
#     tick_kde.get_figure().clf()