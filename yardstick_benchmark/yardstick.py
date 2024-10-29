from time import sleep
from datetime import datetime
from pathlib import Path
import os

import provisioning
import monitoring
import games.minecraft.server
import games.minecraft.workload

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


    def run(self, bots=10):
        provison, nodes = self.provision()
        self.clean(nodes)

        self.set_up_monitoring(nodes[:1])
        server = self.deploy_and_start(nodes[:1])

        if self.workload == "WalkAround":
            workload = games.minecraft.workload.WalkAround(nodes[1:], nodes[0].host, bots_per_node=bots)
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
        dest = Path(f"/var/scratch/{os.getlogin()}/yardstick/{timestamp}")
        self.fetch(dest, nodes)

        self.clean(nodes)
        self.free_provisioned_nodes(provison, nodes)


if __name__ == "__main__":
    ys = Yardstick()
    ys.run()


