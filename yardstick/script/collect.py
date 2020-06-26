import pandas as pd
import re
from argparse import ArgumentParser
from pathlib import Path


def parse_arguments():
    """Parse the commandline arguments."""

    # Prepare the parser
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--directory",
        dest="jobs_directory",
        help="the directory from which to gather output files",
        required=True
    )

    # Parse the arguments
    arguments = parser.parse_args()
    return Path(arguments.jobs_directory)


def collect():
    """Collect the results from the jobs directory"""
    columns = ["name", "timestamp", "players", "max_players", "relative_utilization"]
    data_frame = pd.DataFrame(columns=columns)
    jobs_directory = parse_arguments()
    for job_directory in jobs_directory.iterdir():
        match = re.match("^job_\\d+_(.*)$", job_directory.name)
        if match:
            name = match.group(1)
            server_directory = job_directory / "server-template"
            for csv_file in server_directory.glob("*.csv"):
                partial_data_frame = pd.read_csv(csv_file)
                max_players = int(partial_data_frame["players"].max() / 25) * 25
                partial_data_frame.loc[:, "name"] = name
                partial_data_frame.loc[:, "max_players"] = max_players
                data_frame = data_frame.append(partial_data_frame)
    data_frame.reset_index()
    data_frame.to_csv("output.csv", index=False)


if __name__ == '__main__':
    collect()
