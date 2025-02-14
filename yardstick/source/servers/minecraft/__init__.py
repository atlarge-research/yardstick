
import pkgutil
import importlib
from abc import ABC, abstractmethod
from yardstick.model import RemoteApplication, Node
from pathlib import Path

class Game(object):
    def __init__(self, server: pkgutil.ModuleType, workload: pkgutil.ModuleType):
        self.workload = workload
        self.server = server


def get(config: dict) -> Game:
    name = config["name"]
    server_name = config["server"]["name"]
    workload_name = config["workload"]["name"]
    servers = pkgutil.iter_modules([f"pamuk/games/{name}/server"])
    server = None
    workload = None
    for s in servers:
        print(s)
        if s.name == server_name:
            server = importlib.import_module(f"pamuk.games.{name}.server.{server_name}")
            break
    if server is None:
        raise ValueError(f"server {server_name} not found")
    workloads = pkgutil.iter_modules([f"pamuk/games/{name}/workload"])
    for w in workloads:
        print(w)
        if w.name == workload_name:
            workload = importlib.import_module(f"pamuk.games.{name}.workload.{workload_name}")
            break
    if workload is None:
        raise ValueError(f"workload {workload_name} not found")
    return Game(server.server(), workload)


class Server(ABC):
    @abstractmethod
    def deploy(self) -> None:
        pass
    
    @abstractmethod
    def start(self) -> None:
        pass
    
    @abstractmethod
    def stop(self) -> None:
        pass
    
    @abstractmethod
    def clean(self) -> None:
        pass
    
    @abstractmethod
    def exporters(self) -> list[str]:
        pass

class PaperMC(RemoteApplication):
    def __init__(self, nodes: list[Node]):
        super().__init__(
            "papermc",
            nodes,
            Path(__file__).parent / "papermc_deploy.yml",
            Path(__file__).parent / "papermc_start.yml",
            Path(__file__).parent / "papermc_stop.yml",
            Path(__file__).parent / "papermc_cleanup.yml",
            extravars={
                "hostnames": [n.host for n in nodes],
                "papermc_template": str(Path(__file__).parent / "server.properties.j2"),
            },
        )
