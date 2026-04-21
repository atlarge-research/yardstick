from pathlib import Path
from plumbum import local
import tempfile
import uuid


JOLOKIA_JAR = Path(__file__).parent / "jolokia-agent-jvm-2.5.1-javaagent.jar"
JOLOKIA_PORT = 8778


# https://gist.github.com/tensoralex/a278b39a965d7c509dbd06b57797c6c1
class MinecraftServer:
    """Runs a Minecraft server in apptainer with Jolokia attached.

    The Jolokia Java agent (shipped with this package) is bind-mounted into
    the upstream itzg/minecraft-server image, so no custom container image
    needs to be built or pulled.
    """

    DEFAULT_IMAGE_URL = "docker://itzg/minecraft-server:java25"

    def __init__(self, name: str = "", image_url: str = DEFAULT_IMAGE_URL) -> None:
        self.image_url = image_url
        self.data_dir = tempfile.mkdtemp(dir="/tmp", prefix="mc-data-")
        self.instance_name = name if name else f"mc-{uuid.uuid4()}"
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
