from yardstick_benchmark.provisioning import Das
from yardstick_benchmark.monitoring import Telegraf
from yardstick_benchmark.games.keyverse.server import RedisServer
from yardstick_benchmark.games.keyverse.workload import RedisWorkload
import yardstick_benchmark
from time import sleep
from datetime import datetime, timedelta
from pathlib import Path
import os

from plotter import visualize_bot_metrics, visualize_cpu_metrics, visualize_redis_metrics
from processing import process_metrics

if __name__ == "__main__":

    ### DEPLOYMENT ENVIRONMENT ###
    das = Das()
    # Reserve nodes (1 for Redis server, rest for workload bots)
    num_nodes = 1 + 20
    nodes = das.provision(num=num_nodes, time_s=7200)

    dest = ""

    total_bots = 50 * 20
    bots_per_node = total_bots // (num_nodes - 1)  # Remaining nodes run bots
    test_duration = 600 # Duration for each bot to run
    test_hz = 10  # Hz for bot updates
    grid_radius = 1  # Radius of grid area to subscribe to (For dynamic redis worker)

    try:
        yardstick_benchmark.clean(nodes)

        ### REDIS SERVER ###
        redis_server = RedisServer(nodes[:1])  # First node runs Redis
        redis_server.deploy()

        ### METRICS ###
        telegraf = Telegraf(nodes)
        telegraf.add_input_redis(nodes[0])  # Monitor Redis server node

        ### WORKLOAD DEPLOYMENT###

        wl = RedisWorkload(
            nodes[1:],  # All nodes except the first one run bots
            redis_host=f"redis://{nodes[0].host}:6379",
            duration=timedelta(seconds=test_duration),  # Run for 60 seconds
            bots_per_node=bots_per_node,
            bot_start_delay=timedelta(seconds=0.1),  # Start bots with a delay
            hz=test_hz,
            grid_radius=grid_radius
        )
        wl.deploy()

        ### COMPLETE METRICS SETUP ###
        for node in nodes[1:]:
            telegraf.add_input_keyverse_workers(node, wl.worker_metrics_dir)

        telegraf.deploy()
        telegraf.start()

        ### START WORKLOAD ###
        wl.start()

        # Run test for duration (or monitor actively)
        print(f"Running {total_bots} bots across {num_nodes-1} workers for {test_duration}s")
        for remaining in range(test_duration, 0, -10):
            print(f"Time remaining: {remaining}s")
            sleep(10)
        print("Test completed.")

        ### CLEANUP ###
        wl.stop()
        wl.cleanup()
        redis_server.stop()
        redis_server.cleanup()

        telegraf.stop()
        # telegraf.cleanup()

        timestamp = (
            datetime.now()
            .isoformat(timespec="minutes")
            .replace("-", "")
            .replace(":", "")
        )
        dest = Path(f"/var/scratch/{os.getlogin()}/yardstick/{timestamp}")
        yardstick_benchmark.fetch(dest, nodes)
    finally:
        yardstick_benchmark.clean(nodes)
        das.release(nodes)

    if dest == "":
        print("No destination directory specified. Skipping metric processing.")
        exit(0)

    print("Processing metrics...")
    process_metrics(dest) 

    print("Visualizing bot metrics...")
    visualize_bot_metrics(dest, bots_per_node=bots_per_node)

    print("Visualizing cpu metrics...")
    visualize_cpu_metrics(dest)

    print("Visualizing redis metrics...")
    visualize_redis_metrics(dest)
