import subprocess
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def parse_arguments() -> (Path, int):
    """Parse the commandline arguments."""

    # Prepare the parser
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--directory",
        dest="working_directory",
        help="the directory in which to run the benchmark, containing the benchmark configuration folders",
        required=True
    )
    parser.add_argument(
        "-p",
        "--parallel-jobs",
        dest="parallel_jobs",
        help="the maximum number of parallel jobs that can be used to run the benchmarks",
        required=True
    )

    # Parse the arguments
    arguments = parser.parse_args()
    return Path(arguments.working_directory), int(arguments.parallel_jobs)


if __name__ == '__main__':

    working_directory, parallel = parse_arguments()

    jobs_directory = working_directory / "yardstick-benchmarks"
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        for job_directory in jobs_directory.iterdir():

            # Prepare command arguments
            arguments = ("bash", "-c", f"cd {str(job_directory)}; sbatch --wait run.job")

            # Execute command
            executor.submit(lambda args=arguments: subprocess.run(args))
