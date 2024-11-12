import glob
import pandas as pd
import seaborn
from pathlib import Path

def preprocess_data(location):
    raw_data_files = raw_data_files = glob.glob(f"{location}/**/metrics-*.csv", recursive=True)

    for raw_data_file in raw_data_files:
        metrics_file = Path(raw_data_file)
        keys = {} #rename?
        
        with open(metrics_file) as file:
            for line in file:
                data = line.split(",")
                metric = data[0]

                with open(metrics_file.parent / f"{metric}.csv", "w") as metric_data:
                    metric_data.write(line)

def print_metrics(metrics, location):
    ''' Metrics available:
        CPU
     '''
    supported_metrics = ["CPU"]

    for metric in metrics:
        if metric not in supported_metrics:
            # some kind of soft error
            return

        for file in glob.glob(f"{location}/**/{metric}.csv", recursive=True):
            data = pd.read_csv(file, names = ["timestamp","measurement","core_id","cpu","host","physical_id","time_active", "time_guest", "time_guest_nice", 
                                            "time_idle", "time_iowait", "time_irq", "time_nice", "time_softirq", "time_steal", "time_system", "time_user"])

            print(data)
