from time import sleep
from datetime import datetime, timedelta
from pathlib import Path
import os
import shutil
from collections import defaultdict

import yardstick_benchmark.source.provisioning.provisioning as provisioning
import yardstick_benchmark.source.monitoring as monitoring
import yardstick_benchmark.source.servers.minecraft as server
import yardstick_benchmark.source.workloads as bot

import yardstick_benchmark.source.utils.data_processing.data as data
import yardstick_benchmark.source.utils.data_processing.visualization as viz

import yardstick_benchmark.source.perf_report.performance_report as report

from yardstick_benchmark.model import Node, RemoteAction

class Yardstick():
    ''' 
    Create a Yardstick context object 
        :param environment: Default Das
        :type environment: String

        :param monitoring: Default Telegraf
        :type monitoring: String

        :param server: Default PaperMC
        :type server: String

        :param workload: Default WalkAround
        :type workload: String

        :param metrics: Default All
        :type metrics: String
    '''
    def __init__(self, environment="DAS", monitor="Telegraf", server="PaperMC", workload="WalkAround", metrics="all", dest="output/"):
        self.environment = environment
        self.monitoring = monitor
        self.server = server
        self.workload = workload
        self.metrics = metrics
        self.dest = dest

    def fetch(self, dest: Path, nodes: list[Node]):
        dest.mkdir(parents=True, exist_ok=True)
        return RemoteAction(
            "fetch",
            nodes,
            Path(__file__).parent / "source/provisioning/fetch.yml",
            extravars={"dest": str(dest)},
        ).run()


    def clean(self, nodes: list[Node]):
        return RemoteAction(
            "clean",
            nodes,
            Path(__file__).parent / "source/provisioning/clean.yml",
        ).run()
        
    def provision(self, num_nodes=2, time_s=900):
        #Figure out how to do this nicely
        if self.environment == "DAS":
            das = provisioning.Das()
            nodes = das.provision(num=num_nodes, time_s=time_s)
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
            papermc = server.PaperMC(nodes)
            papermc.deploy()
            papermc.start()

            return papermc

    def stop_server(self, server_handle):
        if self.server == "PaperMC":
            server_handle.stop()
            server_handle.cleanup()


    def run(self, bots=10, duration=60, bots_join_delay=5):
        provison, nodes = self.provision(time_s=duration+900)
        self.clean(nodes)

        self.set_up_monitoring(nodes[:1])
        self.set_data_output_directory()

        server = self.deploy_and_start(nodes[:1])

        if self.workload == "WalkAround":
            workload = bot.WalkAround(nodes[1:], nodes[0].host, bots_per_node=bots, duration=timedelta(seconds=duration), bots_join_delay=timedelta(seconds=bots_join_delay))
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

    def generate_report(self, filename=f"performance_report_{datetime.today().strftime('%Y-%m-%d_%H:%M')}"):
        data_loc = data.preprocess_data(self.dest)

        # List of plot filenames
        plots = defaultdict(list)
        
        # CPU plots
        plots["cpu_box"].append(viz.plot_box_cpu(data_loc + "cpu.csv", f"cpu_box{datetime.now()}"))
        plots["cpu_line"].append(viz.plot_line_cpu(data_loc + "cpu.csv", f"cpu_line{datetime.now()}"))

        # Tick Duration plots
        plots["tick_duration_box"].append(viz.plot_box_tick_duration(data_loc + "minecraft_tick_times.csv", f"tick_duration_box{datetime.now()}"))
        plots["tick_duration_line"].append(viz.plot_line_tick_duration(data_loc + "minecraft_tick_times.csv", f"tick_duration_line{datetime.now()}"))

        # Memory plots
        plots['mem_box'].append(viz.plot_box_mem(data_loc + "mem.csv", f"mem_box{datetime.now()}"))
        plots['mem_line'].append(viz.plot_line_mem(data_loc + "mem.csv", f"mem_line{datetime.now()}"))

        report.render_report(f"{self.dest}/{filename}", plots)


if __name__ == "__main__":
    ys = Yardstick()
    ys.run()
    data.preprocess_data(ys.dest)

