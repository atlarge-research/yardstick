import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import os

sns.set_palette("deep")

def create_plots_directory():
    try:
        os.mkdir("./plots")
    except OSError as error:
        pass

def plot_line_cpu(path, output_file_name):
    data = pd.read_csv(path, names = ["timestamp","measurement","core_id","cpu","host","physical_id","time_active","time_guest","time_guest_nice","time_idle","time_iowait","time_irq","time_nice","time_softirq","time_steal","time_system","time_user"])
    data["timestamp"] = data["timestamp"].transform(lambda x: x - x.min())
    data["timestamp_m"] = data["timestamp"] / 60
    data[data.cpu == "cpu_total"]
    data["time_total"] = data.time_active + data.time_idle
    data["util"] = 100 * data.time_active / data.time_total
    data = data[data.groupby(["timestamp", "cpu"])["time_total"].rank(ascending=False) <= 1]
    data.head()

    custom_params = {"axes.spines.right": False, "axes.spines.top": False}
    sns.set_theme(style="ticks", rc=custom_params)

    f = plt.figure()
    ax = f.add_subplot(111)
    # plt.xlim(0, 17)

    ax = sns.lineplot(data, x="timestamp_m", y="util")
    ax.grid(axis="y")
    ax.set_ylim(bottom=0)
    ax.set_ylabel("CPU utilization [%]")
    ax.set_xlabel("Time [m]")

    create_plots_directory()
    
    ax.get_figure().savefig(f"./plots/{output_file_name}.png")
    ax.get_figure().clf()

    return f"{output_file_name}.png"

def plot_line_tick_duration(path, output_file_name):
    data = pd.read_csv(path, names = ["timestamp", "label", "node", "jolokia_endpoint", "tick_duration_ms"])
    data["timestamp"] = data["timestamp"].transform(lambda x: x - x.min())
    data["timestamp_m"] = data["timestamp"] / 60
    data.head()

    custom_params = {"axes.spines.right": False, "axes.spines.top": False}
    sns.set_theme(style="ticks", rc=custom_params)

    f = plt.figure(figsize=[10, 6])
    ax = f.add_subplot(111)
    plt.xlim(0, 17)

    ax = sns.lineplot(data, x="timestamp_m", y="tick_duration_ms")
    ax.grid(axis="y")
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Tick duration [ms]")
    ax.set_xlabel("Time [m]")

    create_plots_directory()

    ax.get_figure().savefig(f"./plots/{output_file_name}.png")
    ax.get_figure().clf()

    return f"{output_file_name}.png"


def plot_line_mem(path, output_file_name):
    data = pd.read_csv(path, names=["timestamp", "measurement", "host", "active", "available", "available_percent", "buffered", "cached", "commit_limit", 
                                    "committed_as", "dirty", "free", "high_free", "high_total", "huge_page_size", "huge_pages_free", "huge_pages_total", 
                                    "inactive", "low_free", "low_total", "mapped", "page_tables", "shared", "slab", "sreclaimable", "sunreclaim", "swap_cached", 
                                    "swap_free", "swap_total", "total", "used", "used_percent", "vmalloc_chunk", "vmalloc_total", "vmalloc_used", "write_back", "write_back_tmp"])    
    data["timestamp"] = data["timestamp"].transform(lambda x: x - x.min())
    data["timestamp_m"] = data["timestamp"] / 60
    data["used_gb"] = data["used"]/ (10**9)
    data.head()

    custom_params = {"axes.spines.right": False, "axes.spines.top": False}
    sns.set_theme(style="ticks", rc=custom_params)

    f = plt.figure(figsize=[10, 6])
    ax = f.add_subplot(111)
    plt.xlim(0, 17)

    ax = sns.lineplot(data, x="timestamp_m", y="used_gb")
    ax.grid(axis="y")
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Memory Usage [GB]")
    ax.set_xlabel("Time [m]")

    create_plots_directory()

    ax.get_figure().savefig(f"./plots/{output_file_name}.png")
    ax.get_figure().clf()

    return f"{output_file_name}.png"


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
    
    f = plt.figure(figsize=[6,2])
    ax = f.add_subplot(111)
    plt.xlim(0, 10)
    
    sns.boxplot(x=data["util"], width=.4, fill=False, ax=ax)
    ax.set_xlabel("CPU Usage [%]")

    create_plots_directory()
    
    f.tight_layout()
    ax.get_figure().savefig(f"./plots/{output_file_name}.png")
    ax.get_figure().clf()

    return f"{output_file_name}.png"


def plot_box_tick_duration(path, output_file_name):
    data = pd.read_csv(path, names = ["timestamp", "label", "node", "jolokia_endpoint", "tick_duration_ms"])
    data.head()

    custom_params = {"axes.spines.right": False, "axes.spines.top": False, "axes.spines.left": False}
    sns.set_theme(style="whitegrid", rc=custom_params)
    
    f = plt.figure(figsize=[6,2])
    ax = f.add_subplot(111)
    plt.xlim(0, 10)

    sns.boxplot(x=data["tick_duration_ms"], width=.4, fill=False, ax=ax)
    ax.set_xlabel("Tick Duration [ms]")

    create_plots_directory()

    f.tight_layout()
    ax.get_figure().savefig(f"./plots/{output_file_name}.png")
    ax.get_figure().clf()

    return f"{output_file_name}.png"


def plot_box_mem(path, output_file_name):
    data = pd.read_csv(path, names=["timestamp", "measurement", "host", "active", "available", "available_percent", "buffered", "cached", "commit_limit", 
                                    "committed_as", "dirty", "free", "high_free", "high_total", "huge_page_size", "huge_pages_free", "huge_pages_total", 
                                    "inactive", "low_free", "low_total", "mapped", "page_tables", "shared", "slab", "sreclaimable", "sunreclaim", "swap_cached", 
                                    "swap_free", "swap_total", "total", "used", "used_percent", "vmalloc_chunk", "vmalloc_total", "vmalloc_used", "write_back", "write_back_tmp"])
    data["used_gb"] = data["used"]/ (10**9)
    data.head()

    custom_params = {"axes.spines.right": False, "axes.spines.top": False, "axes.spines.left": False}
    sns.set_theme(style="whitegrid", rc=custom_params)
    
    f = plt.figure(figsize=[6,2])
    ax = f.add_subplot(111)
    # plt.xlim(0, 10)

    sns.boxplot(x=data["used_gb"], width=.4, fill=False, ax=ax)
    ax.set_xlabel("Memory Usage")

    create_plots_directory()

    f.tight_layout()
    ax.get_figure().savefig(f"./plots/{output_file_name}.png")
    ax.get_figure().clf()

    return f"{output_file_name}.png"


