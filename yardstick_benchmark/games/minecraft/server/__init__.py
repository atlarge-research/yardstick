from plumbum import local
import tempfile
import uuid


# https://gist.github.com/tensoralex/a278b39a965d7c509dbd06b57797c6c1
class MinecraftServer:
    def __init__(self, name: str = "") -> None:
        self.container_name = "docker://localhost:5000/minecraft-server:java25-jolokia"
        # self.container_name = ""
        self.data_dir = tempfile.mkdtemp(dir="/tmp", prefix="mc-data-")
        self.instance_name = name if name else f"mc-{uuid.uuid4()}"
        self.running = False

    def start(self):
        res = local["apptainer"].run(
            (
                "instance",
                "run",
                "--no-https",
                "--compat",
                "--bind",
                f"{self.data_dir}:/data",
                "--env",
                '"EULA=TRUE"',
                self.container_name,
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
