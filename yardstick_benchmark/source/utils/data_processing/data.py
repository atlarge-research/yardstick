import glob
import pandas as pd
import seaborn as sns
from pathlib import Path
import os
import datetime

def preprocess_data(location):
    try:
        os.mkdir("./output")
    except OSError as error:
        pass

    now = datetime.datetime.today().strftime('%Y-%m-%d_%H:%M')

    try:
        os.mkdir(f"./output/{now}")
    except OSError as error:
        pass

    raw_data_files = raw_data_files = glob.glob(f"{location}/**/metrics-*.csv", recursive=True)

    for raw_data_file in raw_data_files:
        metrics_file = Path(raw_data_file)
        node = Path(metrics_file).parent.parent.name
        
        with open(metrics_file) as file:
            for line in file:
                data = line.split(",")
                metric = data[1]

                output_dir = f"./output/{now}/{node}/"
                try:
                    os.mkdir(f"./output/{now}/{node}")
                except OSError as error:
                    print(error)

                with open(f"./output/{now}/{node}/{metric}.csv", "a+") as metric_data:
                    metric_data.write(line)

    return output_dir

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
