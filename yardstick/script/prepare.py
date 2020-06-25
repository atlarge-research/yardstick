import os
import shutil
from argparse import ArgumentParser
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Union


def parse_arguments() -> (Path, Path):
    """Parse the commandline arguments."""

    # Prepare the parser
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--directory",
        dest="working_directory",
        help="the directory in which the benchmark should be prepared",
        required=True
    )
    parser.add_argument(
        "-c",
        "--client-jar",
        dest="client_jar_file",
        help="the clients' executable JAR file",
        required=True
    )

    # Parse the arguments
    arguments = parser.parse_args()
    working_directory = Path(arguments.working_directory)
    client_jar_file = Path(arguments.client_jar_file)

    # Validate the client jar file
    if not client_jar_file.is_file():
        raise ValueError("The provided server JAR file does not exists or is not a file.")

    return working_directory, client_jar_file


def generate_directory(directory, clear_directory=False):
    """Recreate a directory such that it is available and clean."""
    if clear_directory:
        shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir(parents=True, exist_ok=True)


def get_path(directory, components):
    """Create a path from the given directory and components to a YAML config file."""
    return directory / ("_".join(map(str, components)) + ".yml")


def instantiate_template(template_path: Path, template_map: Dict[str, str]) -> str:
    """Instantiate the given template file by replacing the variables using the dictionary."""
    with template_path.open("r") as template_file:
        template = template_file.read()
        for key, value in template_map.items():
            template = template.replace(f"<<<{key}>>>", value)
        return template


def get_experiment_settings() -> List[Dict[str, Union[str, int, timedelta]]]:
    experiment_settings = list()
    players_per_client = 25
    player_join_interval = timedelta(seconds=1)

    for client_amount in range(13):
        nodes = client_amount + 1
        total_players = client_amount * players_per_client
        client_join_interval = player_join_interval * client_amount
        client_start_delay = timedelta(seconds=60)
        base_run_time = timedelta(minutes=20)

        if players_per_client * client_amount < 100:
            base_run_time = timedelta(minutes=10)
        elif players_per_client * client_amount < 200:
            base_run_time = timedelta(minutes=15)

        client_run_time = base_run_time + player_join_interval * total_players

        experiment_settings.append({
            "NODES": nodes,
            "EXPERIMENT": "6",
            "PLAYERS_PER_CLIENT": players_per_client,
            "CLIENT_AMOUNT": client_amount,
            "CLIENT_START_DELAY": client_start_delay,
            "CLIENT_RUN_TIME": client_run_time,
            "CLIENT_JOIN_INTERVAL": client_join_interval,
            "JOB_TEMPLATE": "opencraft.template.sh",
            "PLAYER_JOIN_INTERVAL": player_join_interval,
        })

    return experiment_settings


def experiment_template(
        server_jar: str,
        client_jar: str,
        server_relative_directory: str,
        settings: Dict[str, Union[str, int, timedelta]]
) -> Dict[str, str]:
    # Add 30 seconds to ensure that the script does not exit too early.
    timeout = settings["CLIENT_START_DELAY"] + settings["CLIENT_RUN_TIME"] + timedelta(seconds=30)

    run_jar = "java -Xmx32768M -Xms4096M -jar"
    experiment = settings['EXPERIMENT']
    bots = settings['PLAYERS_PER_CLIENT']
    client_join_interval = str(int(settings["CLIENT_JOIN_INTERVAL"].total_seconds()))

    template_map = {
        "TIMEOUT": str(timeout),
        "NODES": str(settings["NODES"]),
        "RUN_SERVER_COMMAND": f'cd \\"{server_relative_directory}\\"; {run_jar} \\"{server_jar}\\"',
        "CLIENT_START_DELAY": str(int(settings["CLIENT_START_DELAY"].total_seconds())),
        "CLIENT_AMOUNT": str(settings["CLIENT_AMOUNT"]),
        "RUN_CLIENT_COMMAND": f'{run_jar} "{client_jar}" '
                              f'-e {experiment} '
                              f'-Ebots={bots} '
                              f'-Ejoininterval={client_join_interval} '
                              f'-Eduration={str(int(timeout.total_seconds()))} '  # Bot should not stop running on its own.
                              f'--host "$SERVER_HOSTNAME"',
        "CLIENT_RUN_TIME": str(int(settings["CLIENT_RUN_TIME"].total_seconds())),
        "PLAYER_JOIN_INTERVAL": str(int(settings["PLAYER_JOIN_INTERVAL"].total_seconds())),
        "STOP_SERVER_COMMAND": "stop\\n",  # Need the newline for the command to active in the opencraft server console
    }

    return template_map


def generate_benchmarks(working_directory: Path, client_jar_original: Path):
    # Prepare working directory
    generate_directory(working_directory)

    # Prepare jobs directory
    benchmarks_directory = working_directory / "yardstick-benchmarks"
    generate_directory(benchmarks_directory, clear_directory=True)

    # Copy jar file to working directory
    client_jar_copy = Path(shutil.copy(client_jar_original, working_directory / "client.jar"))

    # Configuration directories
    server_templates_directory = Path(__file__).parent / "server-templates"
    job_templates_directory = Path(__file__).parent / "job-templates"

    # Create job directories and files
    job_index = 0
    for server_template in server_templates_directory.iterdir():
        if not server_template.is_dir():
            raise ValueError(f"{str(server_template)} is not a valid server template directory!")

        template_server_jar = server_template / "server.jar"

        if not template_server_jar.is_file():
            raise ValueError(
                f"There is no server.jar file in the template directory! "
                f"This jar is required for running the server!"
            )

        _, base_server_directory = os.path.split(server_template)
        server_jar_copy = Path(shutil.copy(template_server_jar, working_directory / f"{base_server_directory}_server.jar"))

        for experiment_settings in get_experiment_settings():
            # Prepare job directory
            job_directory = benchmarks_directory / ("job_" + str(job_index) + "_" + base_server_directory)
            job_directory.mkdir(parents=True)
            job_index += 1

            # Move the template to the job directory
            server_directory = job_directory / "server-template"
            shutil.copytree(server_template, server_directory)

            # Prepare relative jar file paths
            server_jar_relative = str(os.path.relpath(server_jar_copy, server_directory))
            client_jar_relative = str(os.path.relpath(client_jar_copy, job_directory))
            server_directory = str(os.path.relpath(server_directory, job_directory))

            # Create job script from template
            job_template_file = job_templates_directory / experiment_settings["JOB_TEMPLATE"]
            template_map = experiment_template(server_jar_relative, client_jar_relative, server_directory, experiment_settings)

            job_script = instantiate_template(job_template_file, template_map)

            # Generate job files in directory
            with (job_directory / "run.job").open("w") as job_script_file:
                job_script_file.write(job_script)


def main():
    working_directory, client_jar = parse_arguments()

    generate_benchmarks(working_directory, client_jar)


if __name__ == '__main__':
    main()
