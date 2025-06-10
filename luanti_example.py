from yardstick_benchmark.provisioning import Das
from yardstick_benchmark.monitoring import Telegraf
from yardstick_benchmark.games.luanti.server import LuantiServer
from yardstick_benchmark.games.luanti.workload import RustWalkAround
import yardstick_benchmark
from time import sleep
from datetime import datetime, timedelta
from pathlib import Path
import os
import shutil

if __name__ == "__main__":
    
    # Set up output directory
    dest = Path(f"/var/scratch/{os.getlogin()}/yardstick/luanti_output")
    if dest.exists():
        shutil.rmtree(dest)

    ### DEPLOYMENT ENVIRONMENT ###

    # The DAS compute cluster is a medium-sized cluster for research and education.
    # We use it in this example to provision bare-metal machines to run our performance
    # evaluation of Luanti servers.
    das = Das()
    # We reserve 2 nodes - one for server, one for bots.
    nodes = das.provision(num=2)

    try:
        # Just in case, we remove data that may have been left from a previous run.
        yardstick_benchmark.clean(nodes)

        ### METRICS ###

        # Telegraf (https://www.influxdata.com/time-series-platform/telegraf/)
        # is the metric collection tool we use to collect performance metrics from the
        # nodes and any applications deployed on these nodes.
        telegraf = Telegraf(nodes)
        # Configure metrics collection for the Luanti server on node 0
        telegraf.add_input_luanti_metrics(nodes[0])
        
        # Perform the actual deployment of Telegraf.
        # This includes downloading the Telegraf executable and preparing configuration
        # files.
        res = telegraf.deploy()
        # Start Telegraf on all remote nodes.
        telegraf.start()

        ### System Under Test (SUT) ###

        # LuantiServer is the Luanti game server whose performance
        # we'll evaluate in this example.
        # We pass a list with all the nodes on which we want to deploy a server.
        # In this example, we only deploy a server on node 0.
        luanti_server = LuantiServer(nodes[:1], game_mode="minetest_game")
        # We perform the deployment, including downloading/setting up the Luanti server
        # and correctly configuring the game's configuration file.
        luanti_server.deploy()
        # We start the game server.
        luanti_server.start()

        ### WORKLOAD ###

        # RustWalkAround creates Rust-based bots from texmodbot that walk around in the game world
        # We deploy the bots on node 1 and connect them to the server on node 0
        wl = RustWalkAround(
            nodes[1:],              # Deploy bots on node 1
            nodes[0].host,          # Connect to server on node 0
            duration=timedelta(seconds=120),  # Run for 2 minutes
            bots_per_node=15,       # 15 bots per node for load testing
            movement_mode="random", # Random movement pattern
            movement_speed=2.0,     # Change direction every 2 seconds
        )
        wl.deploy()
        wl.start()

        # Let the experiment run
        sleep_time = 150  # Run a bit longer than bot duration to capture cleanup
        print(f"Running Luanti benchmark for {sleep_time} seconds")
        print(f"Server on: {nodes[0].host}")
        print(f"Bots on: {nodes[1].host}")
        sleep(sleep_time)

        # Stop the workload and server
        wl.stop()
        wl.cleanup()
        
        luanti_server.stop()
        luanti_server.cleanup()

        telegraf.stop()
        telegraf.cleanup()

        # Fetch all collected data
        yardstick_benchmark.fetch(dest, nodes)
        print(f"Results saved to: {dest}")
        
    finally:
        # Always clean up and release the nodes
        yardstick_benchmark.clean(nodes)
        das.release(nodes)
