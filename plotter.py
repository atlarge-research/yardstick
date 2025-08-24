import math
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import glob
from pathlib import Path
import argparse
from matplotlib.backends.backend_pdf import PdfPages

def visualize_cpu_metrics(dest, max_colors=20):
    """ Visualize CPU metrics from the processed CSV files."""
    dfs = []
    for cpu_file in glob.glob(f"{dest}/**/cpu.csv", recursive=True):
        df = pd.read_csv(cpu_file, names = ["timestamp","measurement","core_id","cpu","host","physical_id","time_active","time_guest","time_guest_nice","time_idle","time_iowait","time_irq","time_nice","time_softirq","time_steal","time_system","time_user"])
        df["node"] = Path(cpu_file).parent.parent.name
        df["timestamp"] = df["timestamp"].transform(lambda x: x - x.min())
        # df["timestamp_m"] = df["timestamp"] / 60
        df = df[df.cpu == "cpu-total"]
        df['time_total'] = df.time_active + df.time_idle
        df['util'] = 100 * df.time_active / df.time_total
        df = df.sort_values("util", ascending=False).drop_duplicates(subset=["timestamp", "cpu"], keep="first")
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    df.head()

    custom_params = {"axes.spines.right": False, "axes.spines.top": False}
    sns.set_theme(style="ticks", rc=custom_params)
    palette = sns.color_palette("husl", n_colors=min(max_colors, len(df["node"].unique())))

    ax = sns.lineplot(df, x="timestamp", y="util", hue="node", palette=palette)
    ax.grid(axis="y")
    ax.set_ylim(bottom=0)
    ax.set_ylabel("CPU utilization [%]")
    ax.set_xlabel("Time [s]")

    num_nodes = len(df["node"].unique())
    if num_nodes > 10:
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(
            handles[:10], labels[:10],  # Show first 10 nodes
            # handles[::(math.ceil(num_nodes/5))], labels[::math.ceil(num_nodes/5)],  # Show every (num_nodes/10) node
            bbox_to_anchor=(1.05, 1),
            loc='upper left',
            title="Node (subset)"
        )
    else:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_title("CPU Utilization Over Time per Node")

    plt.tight_layout()

    plot_path = Path(dest) / "cpu_utilization.pdf"
    plt.savefig(plot_path, format='pdf', dpi=300, bbox_inches='tight')
    print(f"PDF plot saved to: {plot_path}")

    png_path = Path(dest) / "cpu_utilization.png"
    plt.savefig(png_path, dpi=150, bbox_inches='tight')
    print(f"PNG version saved to: {png_path}")

    plt.close()

def visualize_bot_metrics(dest, bots_per_node=1, max_colors=20):
    """
    Visualize bot metrics from the processed CSV files.
    """
    # Load and process all bot metrics
    dfs = []
    for bot_file in glob.glob(f"{dest}/**/bot_metrics_processed.csv", recursive=True):
        try:
            df = pd.read_csv(bot_file)
            df["node"] = Path(bot_file).parent.parent.name
            
            # Convert timestamp to seconds since start and minutes
            df["timestamp"] = pd.to_numeric(df["timestamp"])
            df["timestamp_s"] = (df["timestamp"] - df["timestamp"].min()) / 1000  # Convert ms to s
            
            # Calculate messages per second (throughput)
            df = df.sort_values("timestamp")
            df["msg_per_sec"] = (df["messages_sent"].diff() / df["timestamp_s"].diff())

            # Scale by bots per node
            df["msg_per_sec"] *= bots_per_node
            
            dfs.append(df)
        except Exception as e:
            print(f"Error processing {bot_file}: {e}")

    if not dfs:
        raise ValueError("No bot metrics files found")
    
    df = pd.concat(dfs, ignore_index=True)

    # Visualization
    custom_params = {"axes.spines.right": False, "axes.spines.top": False}
    sns.set_theme(style="ticks", rc=custom_params)

    plt.figure(figsize=(12, 7))

    palette = sns.color_palette("husl", n_colors=min(max_colors, len(df["node"].unique())))
    ax = sns.lineplot(
        data=df,
        x="timestamp_s",
        y="msg_per_sec",
        hue="node",
        palette=palette,
        estimator="mean",
        errorbar=None,
        linewidth=1.5
    )

    max_y = df["msg_per_sec"].max()
    y_top = math.ceil(max_y / 100) * 100
    ax.set_ylim(0, y_top)

    # Calculate and plot overall average
    avg_throughput = df.groupby("node")["msg_per_sec"].mean()
    for node, throughput in avg_throughput.items():
        ax.axhline(
            y=throughput,
            color=palette[list(avg_throughput.index).index(node) % max_colors],
            linestyle="--",
            alpha=0.5
            # label=f"{node} (avg: {throughput:.1f} msg/s)"
        )

    ax.grid(axis="y")
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Throughput [messages/second]")
    ax.set_xlabel("Time [seconds]")
    ax.set_title("Bot Message Throughput per Node")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    num_nodes = len(df["node"].unique())
    if num_nodes > 10:
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(
            handles[:10], labels[:10],  # Show first 10 nodes
            # handles[::(math.ceil(num_nodes/5))], labels[::math.ceil(num_nodes/5)],  # Show every (num_nodes/10) node
            bbox_to_anchor=(1.05, 1),
            loc='upper left',
            title="Node (subset)"
        )
    else:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    # plt.show()

    plot_path = Path(dest) / "bot_throughput.pdf"
    plt.savefig(plot_path, format='pdf', dpi=300, bbox_inches='tight')
    print(f"PDF plot saved to: {plot_path}")

    png_path = Path(dest) / "bot_throughput.png"
    plt.savefig(png_path, dpi=150, bbox_inches='tight')
    print(f"PNG version saved to: {png_path}")

    plt.close()

def visualize_redis_metrics(dest):
    """ 
    Visualize Redis metrics from the processed CSV files.
    """
    dfs = []
    # «column‑index : Redis INFO field»
    cols = [
        "instantaneous_ops_per_sec",     
        "instantaneous_output_kbps",     
        "pubsub_channels",               
        "client_recent_max_output_buffer",  
        "used_cpu_user",
        "used_cpu_sys",
        "used_memory"
    ]

    dfs = []
    for csv_file in glob.glob(f"{dest}/**/redis.csv", recursive=True):
        df = pd.read_csv(csv_file)
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"{csv_file} is missing expected columns: {missing}")
        
        df["timestamp_s"] = df["timestamp"] - df["timestamp"].min()
        df["node"] = Path(csv_file).parent.parent.name

        dfs.append(df[["timestamp_s", "node"] + cols])

    if not dfs:
        raise ValueError("No Redis metrics files found")
    
    data = pd.concat(dfs, ignore_index=True)

    data["cpu_pct_single_core"] = (
        100 * (data.sort_values("timestamp_s").groupby("node")["used_cpu_user"].diff() +
               data.sort_values("timestamp_s").groupby("node")["used_cpu_sys"].diff()) /
        data.sort_values("timestamp_s").groupby("node")["timestamp_s"].diff()
    )

    plot_cols = [
        "instantaneous_ops_per_sec",     
        "instantaneous_output_kbps",     
        "pubsub_channels",               
        "client_recent_max_output_buffer", 
        "cpu_pct_single_core",
        "used_memory"
    ]

    out_dir  = Path(dest)
    pdf_path = out_dir / "redis_metrics.pdf"

    # one chart per metric → one page per metric in the PDF
    with PdfPages(pdf_path) as pdf:
        for metric in plot_cols:
            plt.figure(figsize=(10, 4))
            for node, grp in data.groupby("node"):
                plt.plot(grp["timestamp_s"], grp[metric], label=node)
            plt.xlabel("Time [s]")
            plt.ylabel(metric.replace("_", " ") + (" (%)" if metric == "cpu_pct_single_core" else ""))
            plt.grid(True)
            plt.legend(loc="best")

            png_path = out_dir / f"{metric}.png"
            plt.savefig(png_path, dpi=150, bbox_inches="tight")  # individual PNG
            pdf.savefig()                                        # page in PDF
            plt.close()
            print(f"wrote {png_path}")

    print(f"wrote multi-page PDF → {pdf_path}")



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Visualize bot metrics from processed CSV files.")
    parser.add_argument('--dest', type=str, required=True, help="Directory containing processed bot metrics files")
    args = parser.parse_args()

    # visualize_cpu_metrics(args.dest)
    #visualize_bot_metrics(args.dest, 60)
    visualize_redis_metrics(args.dest)
