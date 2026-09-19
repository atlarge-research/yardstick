"""Provisioning virtual machines on Ubicloud, for `cloud` mode deployments.

Wraps the `ubi` CLI (https://www.ubicloud.com/docs/quick-start/cli). The
control plane stays on the machine running Yardstick; the VMs provisioned
here are the data plane.

Safety
------

Destroying someone else's VM is unrecoverable, so this module is built so
that it structurally cannot:

* **Every destroy is by identifier, never by pattern.** There is no code path
  that lists VMs and deletes the ones whose names look right. A VM is only
  ever destroyed via an identifier this module recorded when it created it.
* **Identifiers are written down before the VM exists.** The ledger entry is
  appended *before* `ubi vm ... create` runs, so a crash between creating a
  VM and learning its id still leaves a record to clean up from.
* **The ledger is the sole authority.** :meth:`Ubicloud.destroy` refuses any
  identifier that is not in it, so a typo or a stale id cannot reach a VM
  Yardstick did not create.
* **There are hard caps** on how many VMs a single call may create and on
  which machine sizes are allowed, so a bad configuration cannot quietly
  provision a fleet.

The ledger is a small JSON file (by default under the user's state
directory). If a run dies without cleaning up, ``Ubicloud(...).release_all()``
or ``yardstick cloud release`` tears down exactly what is recorded in it --
still by identifier, still never by pattern.
"""

import json
import logging
import os
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from yardstick_benchmark.model import Node


logger = logging.getLogger(__name__)


DEFAULT_LEDGER = (
    Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    / "yardstick"
    / "ubicloud-vms.json"
)


class UbicloudError(RuntimeError):
    """A `ubi` CLI invocation failed."""


class UbicloudSafetyError(UbicloudError):
    """A requested operation was refused because it could affect a VM that
    Yardstick did not create."""


@dataclass(frozen=True)
class UbicloudVM:
    """A VM this module created. `ref` is what every command addresses it by."""

    ref: str
    location: str
    name: str
    id: Optional[str] = None
    ip4: Optional[str] = None
    ip6: Optional[str] = None
    unix_user: str = "ubi"

    @property
    def host(self) -> str:
        """Address to reach the VM on. Prefers IPv4 when it was enabled."""
        if self.ip4:
            return self.ip4
        if self.ip6:
            return self.ip6
        raise UbicloudError(f"VM {self.ref} has no reachable address yet")


class Ubicloud:
    """Provision and release Ubicloud VMs for a `cloud` mode deployment.

    Args:
        ssh_public_key: The public key to install on each VM, either the key
            material itself or the name of a key already registered with
            Ubicloud. Defaults to the contents of ``~/.ssh/id_ed25519.pub``
            or ``~/.ssh/id_rsa.pub``, whichever exists.
        location: Ubicloud location to create VMs in.
        size: Machine size. Must be in :attr:`ALLOWED_SIZES`.
        storage_gib: Boot disk size.
        boot_image: Image to boot.
        unix_user: Login user created on the VM.
        max_vms: Hard cap on how many VMs a single provision() call may
            create. Raise it deliberately, not by accident.
        name_prefix: Prefix for generated VM names. Only affects legibility
            in the Ubicloud console -- nothing keys off it, because names are
            never used to decide what to destroy.
        ledger: Path to the JSON file recording created VMs.
        cli: Path to the `ubi` executable.
    """

    DEFAULT_LOCATION = "eu-central-h1"
    DEFAULT_SIZE = "standard-2"
    DEFAULT_STORAGE_GIB = 40
    DEFAULT_BOOT_IMAGE = "ubuntu-noble"
    DEFAULT_WD = "/home/{user}/yardstick"

    #: Sizes a benchmark may ask for. The larger Ubicloud offers
    #: (standard-30, standard-60) are excluded: they are expensive enough
    #: that asking for one should be a deliberate edit here, not a typo in a
    #: configuration file.
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
        if size not in self.ALLOWED_SIZES:
            raise UbicloudSafetyError(
                f"size {size!r} is not allowed. Permitted sizes: "
                f"{', '.join(self.ALLOWED_SIZES)}. Larger sizes are excluded "
                f"deliberately; edit Ubicloud.ALLOWED_SIZES if you really "
                f"need one."
            )
        if storage_gib not in self.ALLOWED_STORAGE_GIB:
            raise UbicloudSafetyError(
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
        self.ledger = Path(ledger) if ledger is not None else DEFAULT_LEDGER
        self.cli = cli

    # ---------------------------------------------------------------- CLI

    def _run(self, *args: str, timeout: float = 300) -> str:
        cmd = [self.cli, *args]
        logger.debug("running %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise UbicloudError(
                f"could not run {self.cli!r}: {exc}. Install the Ubicloud CLI "
                f"(https://www.ubicloud.com/docs/quick-start/cli) and make "
                f"sure it is on PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise UbicloudError(f"{' '.join(cmd)} timed out after {timeout}s") from exc
        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip()
            if "UBI_TOKEN" in message:
                raise UbicloudError(
                    "the Ubicloud CLI needs a personal access token in the "
                    "UBI_TOKEN environment variable"
                )
            raise UbicloudError(f"{' '.join(cmd)} failed: {message}")
        return result.stdout

    # ------------------------------------------------------------- ledger

    def _read_ledger(self) -> List[Dict[str, object]]:
        if not self.ledger.is_file():
            return []
        try:
            data = json.loads(self.ledger.read_text() or "[]")
        except json.JSONDecodeError as exc:
            raise UbicloudError(
                f"ledger {self.ledger} is corrupt ({exc}). Yardstick will not "
                f"destroy anything it cannot read a record for; inspect the "
                f"file and your Ubicloud console by hand."
            ) from exc
        return data if isinstance(data, list) else []

    def _write_ledger(self, records: Sequence[Dict[str, object]]) -> None:
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        # Write-then-rename so an interrupted write can't truncate the record
        # of VMs that exist.
        tmp = self.ledger.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(list(records), indent=2) + "\n")
        tmp.replace(self.ledger)

    def _record(self, vm: UbicloudVM) -> None:
        records = [r for r in self._read_ledger() if r.get("ref") != vm.ref]
        records.append(asdict(vm))
        self._write_ledger(records)

    def _forget(self, ref: str) -> None:
        self._write_ledger([r for r in self._read_ledger() if r.get("ref") != ref])

    def tracked(self) -> List[UbicloudVM]:
        """Every VM recorded in the ledger, i.e. everything Yardstick created
        and has not yet released."""
        return [UbicloudVM(**r) for r in self._read_ledger()]

    # --------------------------------------------------------- lifecycle

    def provision(
        self,
        num: int = 1,
        wd: Optional[str] = None,
        ready_timeout_s: float = 600,
    ) -> List[Node]:
        """Create `num` VMs and return them as :class:`Node`s.

        Each VM is recorded in the ledger *before* it is created, so nothing
        can be created without a record of how to destroy it.
        """
        if num < 1:
            raise ValueError("num must be at least 1")
        if num > self.max_vms:
            raise UbicloudSafetyError(
                f"refusing to create {num} VMs: the cap is {self.max_vms}. "
                f"Pass max_vms= explicitly if you really want more."
            )

        run_id = uuid.uuid4().hex[:8]
        attempted: List[UbicloudVM] = []
        try:
            for index in range(num):
                name = f"{self.name_prefix}-{run_id}-{index}"
                vm = UbicloudVM(
                    ref=f"{self.location}/{name}",
                    location=self.location,
                    name=name,
                    unix_user=self.unix_user,
                )
                # Record before creating: if `create` succeeds but we crash
                # before hearing back -- or fails having partially built a VM
                # -- this entry is what lets it be cleaned up rather than
                # leaked.
                self._record(vm)
                attempted.append(vm)
                self._create(vm)
            created = [self._refresh(vm) for vm in attempted]
            for vm in created:
                self._wait_until_running(vm, timeout_s=ready_timeout_s)
        except BaseException:
            # Never leave half a fleet behind because one VM failed. This
            # includes the VM whose create raised: the call may still have
            # left something behind, so it is torn down too.
            logger.warning("provisioning failed; rolling back %d VM(s)", len(attempted))
            for vm in attempted:
                self._rollback(vm)
            raise

        template = wd or self.DEFAULT_WD
        return [
            Node(vm.host, Path(template.format(user=vm.unix_user))) for vm in created
        ]

    def _create(self, vm: UbicloudVM) -> None:
        logger.info("creating %s (%s, %d GiB)", vm.ref, self.size, self.storage_gib)
        self._run(
            "vm",
            vm.ref,
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

    def _rollback(self, vm: UbicloudVM) -> None:
        """Best-effort teardown of a VM from a failed provision().

        Unlike destroy(), this tolerates the VM not existing -- the create
        may never have got that far -- but it still only ever addresses the
        identifier it recorded, and it always drops the ledger entry so a
        later release_all() doesn't trip over a VM that was never built.
        """
        try:
            self._run("vm", vm.ref, "destroy", "-f")
        except UbicloudError as exc:
            logger.info("rollback: %s could not be destroyed (%s)", vm.ref, exc)
        finally:
            self._forget(vm.ref)

    def _refresh(self, vm: UbicloudVM) -> UbicloudVM:
        """Fill in id and addresses from `ubi vm ... show`, and re-record."""
        fields = self._show(vm.ref, "id", "ip4", "ip6")
        updated = UbicloudVM(
            ref=vm.ref,
            location=vm.location,
            name=vm.name,
            id=fields.get("id") or vm.id,
            ip4=fields.get("ip4") or None,
            ip6=fields.get("ip6") or None,
            unix_user=vm.unix_user,
        )
        self._record(updated)
        return updated

    def _show(self, ref: str, *fields: str) -> Dict[str, str]:
        out = self._run("vm", ref, "show", "-f", ",".join(fields))
        values: Dict[str, str] = {}
        for line in out.splitlines():
            if not line.strip():
                continue
            key, _, value = line.partition("\t")
            if not _:
                key, _, value = line.strip().partition(" ")
            values[key.strip()] = value.strip()
        return values

    def _wait_until_running(self, vm: UbicloudVM, timeout_s: float) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            state = self._show(vm.ref, "state").get("state", "")
            if state == "running":
                logger.info("%s is running", vm.ref)
                return
            time.sleep(5)
        raise UbicloudError(f"{vm.ref} was not running within {timeout_s:.0f}s")

    def destroy(self, ref: str) -> None:
        """Destroy one VM, addressed by an identifier from the ledger.

        Refuses anything the ledger does not know about. This is the only
        place in Yardstick that destroys a VM, and it never discovers its
        target by listing or pattern-matching.
        """
        known = {r.get("ref") for r in self._read_ledger()} | {
            r.get("id") for r in self._read_ledger() if r.get("id")
        }
        if ref not in known:
            raise UbicloudSafetyError(
                f"refusing to destroy {ref!r}: it is not in Yardstick's ledger "
                f"({self.ledger}), so Yardstick did not create it. Destroy it "
                f"from the Ubicloud console if that is really what you want."
            )
        logger.info("destroying %s", ref)
        self._run("vm", ref, "destroy", "-f")
        self._forget(ref)

    def release(self, nodes: Sequence[Node]) -> None:
        """Destroy the VMs backing `nodes`.

        Nodes are matched to ledger entries by address; a node with no
        matching entry is left alone and reported, never guessed at.
        """
        by_address: Dict[str, str] = {}
        for record in self._read_ledger():
            for key in ("ip4", "ip6"):
                address = record.get(key)
                if address:
                    by_address[str(address)] = str(record["ref"])
        unknown = []
        for node in nodes:
            ref = by_address.get(node.host)
            if ref is None:
                unknown.append(node.host)
                continue
            self.destroy(ref)
        if unknown:
            raise UbicloudSafetyError(
                f"no ledger entry for {', '.join(unknown)}; refusing to guess "
                f"which VM to destroy. Use release_all() to tear down "
                f"everything Yardstick created, or check {self.ledger}."
            )

    def release_all(self) -> List[str]:
        """Destroy every VM in the ledger. Returns what was destroyed.

        Still identifier-driven: it walks the records Yardstick wrote, not
        the account's VM list.
        """
        destroyed = []
        for record in list(self._read_ledger()):
            ref = str(record["ref"])
            try:
                self.destroy(ref)
                destroyed.append(ref)
            except Exception as exc:
                logger.error("could not destroy %s: %s", ref, exc)
        return destroyed


def _default_ssh_public_key() -> str:
    for name in ("id_ed25519.pub", "id_rsa.pub"):
        path = Path.home() / ".ssh" / name
        if path.is_file():
            return path.read_text().strip()
    raise UbicloudError(
        "no SSH public key found (~/.ssh/id_ed25519.pub or ~/.ssh/id_rsa.pub). "
        "Pass ssh_public_key= with the key material, or the name of a key "
        "registered with Ubicloud."
    )
