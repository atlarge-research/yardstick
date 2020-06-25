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


def generate_directory(directory):
    """Recreate a directory such that it is available and clean."""
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

    for client_amount in range(13):
        nodes = client_amount + 1
        players_per_client = client_amount * 25
        client_start_delay = timedelta(seconds=60)
        client_run_time = timedelta(minutes=20)

        if players_per_client * client_amount > 150:
            client_run_time = timedelta(minutes=30)

        experiment_settings.append({
            "NODES": nodes,
            "EXPERIMENT": "6",
            "PLAYERS_PER_CLIENT": players_per_client,
            "CLIENT_AMOUNT": client_amount,
            "CLIENT_START_DELAY": client_start_delay,
            "CLIENT_RUN_TIME": client_run_time,
            "JOB_TEMPLATE": "opencraft.template.sh",
        })

    return experiment_settings


def experiment_template(
        server_jar: str,
        client_jar: str,
        settings: Dict[str, Union[str, int, timedelta]]
) -> Dict[str, str]:
    # Add 30 seconds to ensure that the script does not exit too early.
    timeout = settings["CLIENT_START_DELAY"] + settings["CLIENT_RUN_TIME"] + timedelta(seconds=30)

    run_jar = "java -Xmx32768M -Xms4096M -jar"
    experiment = settings['EXPERIMENT']
    bots = settings['PLAYERS_PER_CLIENT']

    template_map = {
        "TIMEOUT": str(timeout),
        "NODES": str(settings["NODES"]),
        "RUN_SERVER_COMMAND": f'{run_jar} "{server_jar}"',
        "CLIENT_START_DELAY": str(settings["CLIENT_START_DELAY"].total_seconds()),
        "CLIENT_AMOUNT": str(settings["CLIENT_AMOUNT"]),
        "RUN_CLIENT_COMMAND": f'{run_jar} {client_jar} -e {experiment} -E bots={bots} --host "$SERVER_HOSTNAME"',
        "CLIENT_RUN_TIME": str(settings["CLIENT_RUN_TIME"].total_seconds()),
        "STOP_SERVER_COMMAND": "stop\n",  # Need the newline for the command to active in the opencraft server console
    }

    return template_map


def generate_benchmarks(working_directory: Path, client_jar_original: Path):
    # Prepare working directory
    generate_directory(working_directory)

    # Prepare jobs directory
    benchmarks_directory = working_directory / "yardstick-benchmarks"
    generate_directory(benchmarks_directory)

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

        base_server_directory = os.path.dirname(server_template)
        server_jar_copy = Path(shutil.copy(template_server_jar, working_directory / f"{base_server_directory}_server.jar"))

        for experiment_settings in get_experiment_settings():
            # Prepare job directory
            job_directory = benchmarks_directory / ("job_" + base_server_directory + "_" + str(job_index))
            job_directory.mkdir(parents=True)
            job_index += 1

            # Move the template to the job directory
            shutil.copytree(server_template, job_directory / "server-template", dirs_exist_ok=True)

            # Prepare relative jar file paths
            server_jar_relative = os.path.relpath(server_jar_copy, job_directory)
            client_jar_relative = os.path.relpath(client_jar_copy, job_directory)

            # Create job script from template
            job_template_file = job_templates_directory / experiment_settings["JOB_TEMPLATE"]
            template_map = experiment_template(str(server_jar_relative), str(client_jar_relative), experiment_settings)

            job_script = instantiate_template(job_template_file, template_map)

            # Generate job files in directory
            with (job_directory / "run.job").open("w") as job_script_file:
                job_script_file.write(job_script)


def main():
    working_directory, client_jar = parse_arguments()

    generate_benchmarks(working_directory, client_jar)


if __name__ == '__main__':
    main()
