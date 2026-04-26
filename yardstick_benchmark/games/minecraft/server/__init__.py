from pathlib import Path
from plumbum import local
import tempfile
import uuid

from yardstick_benchmark.util import random_string


JOLOKIA_JAR = Path(__file__).parent / "jolokia-agent-jvm-2.5.1-javaagent.jar"
JOLOKIA_PORT = 8778
RCON_PORT = 25575


# https://gist.github.com/tensoralex/a278b39a965d7c509dbd06b57797c6c1
class MinecraftServer:
    """Runs a Minecraft server in apptainer with Jolokia + RCON attached.

    The Jolokia Java agent (shipped with this package) is bind-mounted into
    the upstream itzg/minecraft-server image, so no custom container image
    needs to be built or pulled. RCON is enabled with an auto-generated
    password (override via the rcon_password constructor kwarg) and is used
    for in-band server commands like set_world_spawn().
    """

    DEFAULT_IMAGE_URL = "docker://itzg/minecraft-server:java25"

    def __init__(
        self,
        name: str = "",
        image_url: str = DEFAULT_IMAGE_URL,
        rcon_password: str = "",
    ) -> None:
        self.image_url = image_url
        self.data_dir = tempfile.mkdtemp(dir="/tmp", prefix="mc-data-")
        self.instance_name = name if name else f"mc-{uuid.uuid4()}"
        self.rcon_password = rcon_password or random_string(16)
        self.running = False

    def start(self):
        jvm_opts = (
            f"-javaagent:/opt/jolokia.jar=port={JOLOKIA_PORT},host=0.0.0.0"
        )
        res = local["apptainer"].run(
            (
                "instance",
                "run",
                "--no-https",
                "--compat",
                "--bind",
                f"{self.data_dir}:/data",
                "--bind",
                f"{JOLOKIA_JAR}:/opt/jolokia.jar",
                "--env",
                "EULA=TRUE",
                "--env",
                "ONLINE_MODE=false",
                "--env",
                "ENABLE_JMX=true",
                "--env",
                "ENABLE_RCON=true",
                "--env",
                f"RCON_PASSWORD={self.rcon_password}",
                "--env",
                f"JVM_OPTS={jvm_opts}",
                self.image_url,
                self.instance_name,
            )
        )
        if res[0] == 0:
            self.running = True
        else:
            raise RuntimeError(
                f"Failed to start Minecraft server instance {self.instance_name}"
            )

    def stop(self):
        res = local["apptainer"].run(("instance", "stop", self.instance_name))
        if res[0] == 0:
            self.running = False
        else:
            raise RuntimeError(
                f"Failed to stop Minecraft server instance {self.instance_name}"
            )

    def rcon(self, *commands: str) -> None:
        """Send one or more commands to the running server via RCON.

        Uses the rcon-cli binary that itzg/minecraft-server bundles by
        execing straight into the running instance, so no extra container
        is launched. The server must already be started and accepting
        connections (use a TCP-readiness check on the game port before
        calling this).
        """
        if not commands:
            return
        local["apptainer"].run(
            (
                "exec",
                "--env", "RCON_HOST=localhost",
                "--env", f"RCON_PORT={RCON_PORT}",
                "--env", f"RCON_PASSWORD={self.rcon_password}",
                f"instance://{self.instance_name}",
                "rcon-cli",
                *commands,
            )
        )

    def set_world_spawn(self, x: int, z: int, y: int = 4) -> None:
        """Move the world spawn to (x, y, z) via RCON."""
        self.rcon(f"setworldspawn {x} {y} {z}")
