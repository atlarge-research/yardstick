import glob
import json
from pathlib import Path
import argparse

def process_metrics(dest):
    """
    Process all Telegraf metrics CSV files in the node directories.
    Creates separate CSV files for each metric type in the same directory.
    """
    raw_data_files = glob.glob(f"{dest}/**/metrics-*.csv", recursive=True)
    
    for raw_data_file in raw_data_files:
        metrics_file = Path(raw_data_file)
        keys = {}
        with open(metrics_file) as fin:
            for line in fin:
                first_delim = line.find(",")
                second_delim = line.find(",", first_delim+1)
                key = line[first_delim+1:second_delim]
                if key not in keys:
                    keys[key] = open(metrics_file.parent / f"{key}.csv", "w+")
                keys[key].write(line)
        for key, fd in keys.items():
            fd.close()

    # Process Redis metrics
    raw_redis_files = glob.glob(f"{dest}/**/redis-metrics-*.csv", recursive=True)
    
    for raw_redis_file in raw_redis_files:
        redis_file = Path(raw_redis_file)
        keys = {}
        with open(redis_file) as fin:
            header = fin.readline()  # Read header line
            for line in fin:
                first_delim = line.find(",")
                second_delim = line.find(",", first_delim+1)
                key = line[first_delim+1:second_delim]
                if key not in keys:
                    outfile = redis_file.parent / f"{key}.csv"
                    keys[key] = open(outfile, "w+")

                    if key.lower() == "redis":
                        keys[key].write(header)
                keys[key].write(line)
        for key, fd in keys.items():
            fd.close()



    # Process new JSON bot metrics
    bot_metrics_files = glob.glob(f"{dest}/**/bot*_metrics", recursive=True)
    #print("Found bot metric files:", bot_metrics_files)
    
    for metrics_file in bot_metrics_files:
        metrics_file = Path(metrics_file)
        output_file = metrics_file.parent / f"bot_metrics_processed.csv"
        
        with open(metrics_file) as fin, open(output_file, "w") as fout:
            # Write CSV header
            fout.write("timestamp,bot_id,messages_sent,avg_latency_ms\n")
            
            for line in fin:
                try:
                    data = json.loads(line)
                    fout.write(
                        f"{data['timestamp']},"
                        f"{data['bot_id']},"
                        f"{data['messages_sent']},"
                        f"{data['avg_latency_ms']}\n"
                    )
                except json.JSONDecodeError as e:
                    print(f"Error parsing line in {metrics_file}: {e}")  

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Telegraf metrics files.")
    parser.add_argument('--dest', type=str, required=True, help="Directory containing Telegraf metrics files")
    args = parser.parse_args()
    
    process_metrics(args.dest)