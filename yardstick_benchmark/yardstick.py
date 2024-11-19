from time import sleep
from datetime import datetime, timedelta
from pathlib import Path
import os
import shutil

import provisioning
import monitoring
import games.minecraft.server
import games.minecraft.workload

import data

from model import Node, RemoteAction

class Yardstick():
    ''' Default Values: 
        Environment: DAS
        Monitoring: Telegraf
        Server: PaperMC
        Workload: WalkAround
        Metrics: All
    '''
    def __init__(self, environment="DAS", monitor="Telegraf", server="PaperMC", workload="WalkAround", metrics="all"):
        self.environment = environment
        self.monitoring = monitor
        self.server = server
        self.workload = workload
        self.metrics = metrics
        self.dest = None

    def fetch(self, dest: Path, nodes: list[Node]):
        dest.mkdir(parents=True, exist_ok=True)
        return RemoteAction(
            "fetch",
            nodes,
            Path(__file__).parent / "fetch.yml",
            extravars={"dest": str(dest)},
        ).run()


    def clean(self, nodes: list[Node]):
        return RemoteAction(
            "clean",
            nodes,
            Path(__file__).parent / "clean.yml",
        ).run()
    
    def provision(self, num_nodes=2):
        #Figure out how to do this nicely
        if self.environment == "DAS":
            das = provisioning.Das()
            nodes = das.provision(num=num_nodes)
            return das, nodes

        return None
    
    def free_provisioned_nodes(self, handle, nodes):
        handle.release(nodes)
    
    def set_up_monitoring(self, nodes):
        if self.monitoring == "Telegraf":
            telegraf = monitoring.Telegraf(nodes)
            for node in nodes:
                telegraf.add_input_jolokia_agent(node)
                telegraf.add_input_execd_minecraft_ticks(node)

                telegraf.deploy()
                telegraf.start()

    def set_data_output_directory(self, dir="yardstick/output"):
        if self.environment == "DAS":
            self.dest = Path(f"/var/scratch/{os.getlogin()}/{dir}")
            if self.dest.exists():
                shutil.rmtree(self.dest)

    def get_metrics():
        pass

    
    def deploy_and_start(self, nodes):
        if self.server == "PaperMC":
            papermc = games.minecraft.server.PaperMC(nodes)
            papermc.deploy()
            papermc.start()

            return papermc

    def stop_server(self, server_handle):
        if self.server == "PaperMC":
            server_handle.stop()
            server_handle.cleanup()


    def run(self, bots=10, duration=60, bots_join_delay=5):
        provison, nodes = self.provision()
        self.clean(nodes)

        self.set_up_monitoring(nodes[:1])
        self.set_data_output_directory()

        server = self.deploy_and_start(nodes[:1])

        if self.workload == "WalkAround":
            workload = games.minecraft.workload.WalkAround(nodes[1:], nodes[0].host, bots_per_node=bots, duration=timedelta(seconds=duration), bots_join_delay=timedelta(seconds=bots_join_delay))
            workload.deploy()
            workload.start()

        sleep(10)

        self.stop_server(server)

        timestamp = (
            datetime.now()
            .isoformat(timespec="minutes")
            .replace("-", "")
            .replace(":", "")
        )
        self.fetch(self.dest, nodes)

        self.clean(nodes)
        self.free_provisioned_nodes(provison, nodes)

    def run_multiple():
        pass


if __name__ == "__main__":
    ys = Yardstick()
    ys.run()
    data.preprocess_data(ys.dest)

