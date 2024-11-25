from yardstick_benchmark_2.model import RemoteApplication, Node
import os
from enum import Enum
import sys
from pathlib import Path

class DiskStat(RemoteApplication):
    """ Runs diskstat collection script that collects disk data from Linux /proc/diskstat every 100 milliseconds 
    """

    def __init__(self, nodes: list[Node]):
        """ 
        Args:
            nodes (list[Node]): The nodes on which to run diskstat collection
        """
        super().__init__(
            "diskstat",
            nodes,
            Path(__file__).parent / "diskstat_deploy.yml",
            Path(__file__).parent / "diskstat_start.yml",
            Path(__file__).parent / "diskstat_stop.yml",
            Path(__file__).parent / "diskstat_cleanup.yml",
            extravars={
                "diskstat_script": os.path.join(
                    os.path.dirname(__file__), "collect_diskstat.sh"
                )
            }
        )


class Telegraf(RemoteApplication):
    """Runs the Telegraf metric collection tool
    (https://www.influxdata.com/time-series-platform/telegraf/) on remote nodes.
    """

    def __init__(self, nodes: list[Node]):
        """Create a new instance to run Telegraf on the given nodes.

        Args:
            nodes (list[Node]): The nodes on which to run Telegraf
        """
        super().__init__(
            "telegraf",
            nodes,
            Path(__file__).parent / "telegraf_deploy.yml",
            Path(__file__).parent / "telegraf_start.yml",
            Path(__file__).parent / "telegraf_stop.yml",
            Path(__file__).parent / "telegraf_cleanup.yml",
            extravars={
                "config_template": os.path.join(
                    os.path.dirname(__file__), "telegraf.conf.j2"
                ),
            },
        )

    def add_input_jolokia_agent(self, node: Node):
        """Configure Telegraf to run the Jolokia agent input on the given node.
        The node should be present in the list of nodes given when constructing
        this Telegraf object.

        Args:
            node (Node): The node on which to run the Jolokia agent input
        """
        assert node in self.nodes
        self.extravars.setdefault("jolokia2_agent", []).append(node.host)

    def add_input_execd_minecraft_ticks(self, node: Node):
        """Configure Telegraf to run an execd input on the given node to collect
        the tick duration metric from a Minecraft server.

        Args:
            node (Node): The node on which to run the execd input
        """
        self.extravars.setdefault("execd_minecraft_ticks", []).append(node.host)
        self.extravars["jolokia_get_minecraft_tick_script_path"] = os.path.join(
            os.path.dirname(__file__), "jolokia_get_minecraft_tick.py"
        )
        this_host = self.inv["all"]["hosts"][node.host]
        self.inv.setdefault("minecraft_servers", {}).setdefault("hosts", {})[
            node.host
        ] = this_host

    def add_fsys_activity_collection(self, node):
        self.extravars.setdefault("execd_fs_activity", []).append(node.host)
        self.extravars["fs_post_processing_script_path"] = os.path.join(
            os.path.dirname(__file__), "fs_post_processing.py"
        )
        this_host = self.inv["all"]["hosts"][node.host]
        self.inv.setdefault("minecraft_servers", {}).setdefault("hosts", {})[
            node.host
        ] = this_host
