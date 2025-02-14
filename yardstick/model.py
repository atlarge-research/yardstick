from dataclasses import dataclass
import ansible_runner
import tempfile
import shutil
from pathlib import Path
import string
import random
import os
from typing import Optional


@dataclass(frozen=True)
class Node(object):
    host: str
    wd: Path


def _gen_wd_name(name, node_wd) -> str:
    alphabet = string.ascii_lowercase + string.digits
    hash = "".join(random.choices(alphabet, k=8))
    return str(node_wd / f"{name}-{hash}")


def _gen_inv(name: str, nodes: list[Node]) -> dict:
    hosts = {
        node.host: {"node_wd": str(node.wd), "wd": _gen_wd_name(name, node.wd)}
        for node in nodes
    }
    return {"all": {"hosts": hosts}}


class RemoteAction(object):
    def __init__(
        self,
        name: str,
        nodes: list[Node],
        script: Path,
        envvars: dict = {},
        extravars: dict = {},
        inv: Optional[dict] = None,
    ):
        self.name = name
        self.hosts = {
            node.host: {"node_wd": node.wd, "wd": _gen_wd_name(name, node.wd)}
            for node in nodes
        }
        self.inv = inv if inv is not None else _gen_inv(name, nodes)
        self.script = script
        self.envvars = envvars
        self.extravars = extravars

    def run(self):
        assert self.script.is_file()

        self.private_data_dir = tempfile.mkdtemp(prefix="yardstick-")
        res = ansible_runner.interface.run(
            private_data_dir=self.private_data_dir,
            playbook=str(self.script),
            inventory=self.inv,
            envvars=self.envvars,
            extravars=self.extravars,
            settings={
                "pipelining": True,
                "ssh_args": "-o ControlMaster=auto -o ControlPersist=60s",
                "deprecation_warnings": False,
            },
        )
        shutil.rmtree(self.private_data_dir)
        return res


class RemoteApplication(object):
    def __init__(
        self,
        name: str,
        nodes: list[Node],
        deploy_script: Path,
        start_script: Path,
        stop_script: Path,
        cleanup_script: Path,
        envvars: dict = {},
        extravars: dict = {},
    ):
        self.nodes = nodes
        self.inv = _gen_inv(name, nodes)
        self.envvars = envvars
        self.extravars = extravars
        self.deploy_action = RemoteAction(
            name, nodes, deploy_script, envvars, extravars, self.inv
        )
        self.start_action = RemoteAction(
            name, nodes, start_script, envvars, extravars, self.inv
        )
        self.stop_action = RemoteAction(
            name, nodes, stop_script, envvars, extravars, self.inv
        )
        self.cleanup_action = RemoteAction(
            name, nodes, cleanup_script, envvars, extravars, self.inv
        )

    def deploy(self):
        return self.deploy_action.run()

    def start(self):
        return self.start_action.run()

    def stop(self):
        return self.stop_action.run()

    def cleanup(self):
        return self.cleanup_action.run()
