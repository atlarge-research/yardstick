"""Provisioning virtual machines on Ubicloud, for `cloud` mode deployments.

Wraps the `ubi` CLI (https://www.ubicloud.com/docs/quick-start/cli). The
control plane stays on the machine running Yardstick; the VMs provisioned
here are the data plane.

The safety rules -- release only by recorded identifier, record before
create, roll back a partial fleet, never sweep the provider's inventory --
live in :class:`~yardstick_benchmark.provisioning.Provisioner`. What this
module adds on top is Ubicloud-specific: machine sizes, images, the SSH key
to install, and a cap on how much can be created at once.
"""

import logging
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from yardstick_benchmark.model import Node
from yardstick_benchmark.provisioning import (
    Provisioner,
    ProvisioningError,
    ProvisioningSafetyError,
)


logger = logging.getLogger(__name__)


# Kept as aliases so callers can catch Ubicloud-specific problems by name
# while the shared machinery raises the generic ones.
UbicloudError = ProvisioningError
UbicloudSafetyError = ProvisioningSafetyError


class Ubicloud(Provisioner):
    """Provision and release Ubicloud VMs.

    Args:
        ssh_public_key: Public key to install on each VM, either the key
            material itself or the name of a key already registered with
            Ubicloud. Defaults to ``~/.ssh/id_ed25519.pub`` or
            ``~/.ssh/id_rsa.pub``, whichever exists.
        location: Ubicloud location to create VMs in.
        size: Machine size, from :attr:`ALLOWED_SIZES`.
        storage_gib: Boot disk size.
        boot_image: Image to boot.
        unix_user: Login user created on the VM.
        max_vms: Hard cap on VMs per provision() call.
        name_prefix: Prefix for generated VM names. Affects legibility in the
            Ubicloud console only -- nothing keys off it, because names are
            never used to decide what to destroy.
        ledger: Path to the JSON file recording created VMs.
        cli: Path to the `ubi` executable.
    """

    LEDGER_NAME = "ubicloud-vms.json"

    DEFAULT_LOCATION = "eu-central-h1"
    DEFAULT_BOOT_IMAGE = "ubuntu-noble"
    DEFAULT_WD = "/home/{user}/yardstick"

    # Ubicloud's standard line is 4 GB of RAM per vCPU (standard-2 is 2 vCPU
    # / 8 GB), scaling linearly.
    #
    # Sizing for Minecraft: the server's tick loop is dominated by
    # single-thread performance, but chunk generation -- which the worldgen
    # workload exists to stress -- does use several cores. Community guidance
    # puts a vanilla/Paper server at roughly 6 GB for 10-20 players, with
    # 2-4 cores adequate for small servers and more wanted as player counts
    # grow. MinecraftServer defaults to a 4 GB JVM heap, so the server node
    # needs meaningfully more than that once the JVM's own overhead and the
    # OS are accounted for.
    #
    # Hence standard-4 (4 vCPU / 16 GB) for the game server: comfortable
    # headroom over a 4 GB heap and enough cores for parallel chunk
    # generation. The emulated players are far lighter -- Mineflayer keeps a
    # world view per bot but does little computation -- so standard-2
    # (2 vCPU / 8 GB) is the default there. Whether that holds for a given
    # bot count is not a guess worth trusting: yardstick_benchmark.saturation
    # checks the workload nodes' CPU, memory and swap after every run and
    # says so if they were the bottleneck.
    DEFAULT_SERVER_SIZE = "standard-4"
    DEFAULT_WORKLOAD_SIZE = "standard-2"
    DEFAULT_SIZE = DEFAULT_WORKLOAD_SIZE
    DEFAULT_STORAGE_GIB = 40

    #: Sizes a benchmark may ask for. standard-30 and standard-60 are
    #: excluded: they are expensive enough that using one should be a
    #: deliberate edit here, not a typo in a configuration file.
    ALLOWED_SIZES = (
        "burstable-1",
        "burstable-2",
        "standard-2",
        "standard-4",
        "standard-8",
        "standard-16",
    )

    ALLOWED_STORAGE_GIB = (10, 20, 40, 80, 160, 320, 600, 640, 1200, 2400)

    #: Cap on VMs per provision() call.
    MAX_VMS = 8

    def __init__(
        self,
        ssh_public_key: Optional[str] = None,
        location: str = DEFAULT_LOCATION,
        size: str = DEFAULT_SIZE,
        storage_gib: int = DEFAULT_STORAGE_GIB,
        boot_image: str = DEFAULT_BOOT_IMAGE,
        unix_user: str = "ubi",
        max_vms: int = MAX_VMS,
        name_prefix: str = "yardstick",
        ledger: Optional[Path] = None,
        cli: str = "ubi",
    ) -> None:
        super().__init__(ledger=ledger)
        if size not in self.ALLOWED_SIZES:
            raise ProvisioningSafetyError(
                f"size {size!r} is not allowed. Permitted sizes: "
                f"{', '.join(self.ALLOWED_SIZES)}. Larger sizes are excluded "
                f"deliberately; edit Ubicloud.ALLOWED_SIZES if you really "
                f"need one."
            )
        if storage_gib not in self.ALLOWED_STORAGE_GIB:
            raise ProvisioningSafetyError(
                f"storage_gib {storage_gib} is not a valid Ubicloud storage "
                f"size. Permitted: {', '.join(map(str, self.ALLOWED_STORAGE_GIB))}"
            )
        self.ssh_public_key = ssh_public_key or _default_ssh_public_key()
        self.location = location
        self.size = size
        self.storage_gib = storage_gib
        self.boot_image = boot_image
        self.unix_user = unix_user
        self.max_vms = max_vms
        self.name_prefix = name_prefix
        self.cli = cli

    # ---------------------------------------------------------------- CLI

    def _run(self, *args: str, timeout: float = 300) -> str:
        cmd = [self.cli, *args]
        logger.debug("running %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, check=False
            )
        except FileNotFoundError as exc:
            raise ProvisioningError(
                f"could not run {self.cli!r}: {exc}. Install the Ubicloud CLI "
                f"(https://www.ubicloud.com/docs/quick-start/cli) and make "
                f"sure it is on PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ProvisioningError(
                f"{' '.join(cmd)} timed out after {timeout}s"
            ) from exc
        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip()
            if "UBI_TOKEN" in message:
                raise ProvisioningError(
                    "the Ubicloud CLI needs a personal access token in the "
                    "UBI_TOKEN environment variable. See "
                    "https://www.ubicloud.com/docs/quick-start/cli"
                )
            raise ProvisioningError(f"{' '.join(cmd)} failed: {message}")
        return result.stdout

    def _show(self, ref: str, *fields: str) -> Dict[str, str]:
        """Parse `ubi vm ... show -f a,b,c`, which prints one "key: value"
        line per field. A field with no value prints as a bare "key:", so the
        separator has to be the first colon rather than whitespace.
        """
        out = self._run("vm", ref, "show", "-f", ",".join(fields))
        values: Dict[str, str] = {}
        for line in out.splitlines():
            if not line.strip():
                continue
            key, sep, value = line.partition(":")
            if not sep:
                # Fall back to whitespace for a tabular variant.
                key, _, value = line.strip().partition(" ")
            values[key.strip()] = value.strip()
        return values

    # ------------------------------------------------------- Provisioner

    def _acquire(
        self,
        num: int,
        wd: Optional[str] = None,
        ready_timeout_s: float = 600,
        **_: Any,
    ) -> List[Dict[str, Any]]:
        if num > self.max_vms:
            raise ProvisioningSafetyError(
                f"refusing to create {num} VMs: the cap is {self.max_vms}. "
                f"Pass max_vms= explicitly if you really want more."
            )
        run_id = uuid.uuid4().hex[:8]
        template = wd or self.DEFAULT_WD
        refs: List[str] = []
        for index in range(num):
            name = f"{self.name_prefix}-{run_id}-{index}"
            ref = f"{self.location}/{name}"
            # Record before creating: if `create` succeeds but we crash before
            # hearing back -- or fails having partially built a VM -- this
            # entry is what lets it be cleaned up rather than leaked.
            self._pre_record(
                ref,
                host=None,
                name=name,
                location=self.location,
                unix_user=self.unix_user,
                wd=template.format(user=self.unix_user),
            )
            refs.append(ref)
            logger.info("creating %s (%s, %d GiB)", ref, self.size, self.storage_gib)
            self._run(
                "vm",
                ref,
                "create",
                "-s",
                self.size,
                "-S",
                str(self.storage_gib),
                "-b",
                self.boot_image,
                "-u",
                self.unix_user,
                self.ssh_public_key,
            )
        for ref in refs:
            self._wait_until_running(ref, ready_timeout_s)
        return [self._refresh(ref) for ref in refs]

    def _refresh(self, ref: str) -> Dict[str, Any]:
        """Fill in id and addresses from `ubi vm ... show`, and re-record."""
        record = dict(self.ledger.get(ref) or {"ref": ref})
        fields = self._show(ref, "id", "ip4", "ip6")
        ip4 = fields.get("ip4") or None
        ip6 = fields.get("ip6") or None
        host = ip4 or ip6
        if not host:
            raise ProvisioningError(f"VM {ref} has no reachable address")
        record.update(id=fields.get("id") or None, ip4=ip4, ip6=ip6, host=host)
        self.ledger.record(**record)
        return record

    def _wait_until_running(self, ref: str, timeout_s: float) -> None:
        import time

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self._show(ref, "state").get("state", "") == "running":
                logger.info("%s is running", ref)
                return
            time.sleep(5)
        raise ProvisioningError(f"{ref} was not running within {timeout_s:.0f}s")

    def _release_one(self, record: Dict[str, Any]) -> None:
        self._run("vm", str(record["ref"]), "destroy", "-f")

    def node_for(self, record: Dict[str, Any]) -> Node:
        return Node(str(record["host"]), Path(str(record["wd"])))


def _default_ssh_public_key() -> str:
    for name in ("id_ed25519.pub", "id_rsa.pub"):
        path = Path.home() / ".ssh" / name
        if path.is_file():
            return path.read_text().strip()
    raise ProvisioningError(
        "no SSH public key found (~/.ssh/id_ed25519.pub or ~/.ssh/id_rsa.pub). "
        "Set ssh_public_key in the [provisioning] section of your config, to "
        "either the key material or the name of a key registered with "
        "Ubicloud."
    )
