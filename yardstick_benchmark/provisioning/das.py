"""Provisioning nodes on a DAS cluster via `preserve`, for `cluster` mode.

Unlike a cloud provider, `preserve` does not create machines -- it hands out
time-boxed reservations on machines that already exist. The resource this
provisioner acquires and releases is therefore the *reservation*, not the
node: releasing means cancelling reservation N, which is exactly the kind of
identifier-addressed operation the base class is built around.

Recording reservations in the ledger matters here for the same reason it does
in the cloud: a run that dies without cancelling leaves nodes reserved (and
unusable by anyone else) until the reservation expires. ``release_all()``
from a later process cleans that up.
"""

import getpass
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from plumbum import local

from yardstick_benchmark.model import Node
from yardstick_benchmark.provisioning import Provisioner, ProvisioningError


logger = logging.getLogger(__name__)


class Das(Provisioner):
    """Reserve nodes on a DAS cluster with `preserve`.

    Args:
        wd: Template for each node's working directory. ``{user}`` and
            ``{host}`` are substituted.
        ledger: Path to the JSON file recording reservations.
    """

    LEDGER_NAME = "das-reservations.json"

    DEFAULT_WD = "/local/{user}/yardstick/{host}"
    DEFAULT_TIME_S = 900

    def __init__(
        self,
        wd: str = DEFAULT_WD,
        ledger: Optional[Path] = None,
    ):
        super().__init__(ledger=ledger)
        self.wd = wd

    # ------------------------------------------------------------ preserve

    def _preserve(self, *args: str) -> str:
        try:
            return local["preserve"][args]()
        except Exception as exc:
            raise ProvisioningError(f"preserve {' '.join(args)} failed: {exc}") from exc

    def _reservations(self) -> Dict[int, Dict[str, Any]]:
        """Parse `preserve -llist` into {number: {state, hosts}}."""
        out = self._preserve("-llist")
        reservations: Dict[int, Dict[str, Any]] = {}
        for line in out.split("\n")[3:]:
            parts = line.split()
            if not parts:
                continue
            try:
                number = int(parts[0])
            except ValueError:
                continue
            reservations[number] = {
                "state": parts[6] if len(parts) > 6 else "",
                "hosts": parts[8:] if len(parts) > 8 else [],
            }
        return reservations

    def _wait_until_ready(self, number: int, timeout_s: float) -> List[str]:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            reservation = self._reservations().get(number)
            if reservation and reservation["state"] == "R":
                return list(reservation["hosts"])
            time.sleep(1)
        raise ProvisioningError(
            f"reservation {number} was not ready within {timeout_s:.0f}s"
        )

    # ------------------------------------------------------- Provisioner

    def _acquire(
        self,
        num: int,
        time_s: int = DEFAULT_TIME_S,
        wd: Optional[str] = None,
        ready_timeout_s: float = 600,
        **_: Any,
    ) -> List[Dict[str, Any]]:
        out = self._preserve("-np", str(num), "-t", str(time_s))
        try:
            number = int(out.split()[2][:-1])
        except (IndexError, ValueError) as exc:
            raise ProvisioningError(
                f"could not read a reservation number out of preserve's output: {out!r}"
            ) from exc

        # One ledger entry per reservation, written as soon as we know the
        # number -- before waiting for it to become ready, so an interrupted
        # wait still leaves the reservation cancellable.
        ref = str(number)
        self._pre_record(ref, host=None, reservation=number, hosts=[])
        hosts = self._wait_until_ready(number, ready_timeout_s)

        user = getpass.getuser()
        template = wd or self.wd
        records = []
        for host in hosts:
            records.append(
                {
                    "ref": ref,
                    "host": host,
                    "reservation": number,
                    "hosts": hosts,
                    "wd": template.format(user=user, host=host),
                }
            )
        # The reservation is one resource covering several hosts; record it
        # once, with every host it covers, so release() can match any of them
        # back to the reservation to cancel.
        self.ledger.record(
            ref,
            host=hosts[0] if hosts else None,
            reservation=number,
            hosts=hosts,
            wd=template,
        )
        return records

    def _release_one(self, record: Dict[str, Any]) -> None:
        self._preserve("-c", str(record["reservation"]))

    def node_for(self, record: Dict[str, Any]) -> Node:
        return Node(str(record["host"]), Path(str(record["wd"])))

    def release(self, nodes) -> None:
        """Cancel the reservations covering `nodes`.

        A reservation covers several hosts at once, so releasing any node
        cancels the whole reservation it belongs to -- there is no way to give
        back half a reservation.
        """
        wanted = {node.host for node in nodes}
        refs = []
        for record in self.ledger.records():
            hosts = set(record.get("hosts") or [])
            if wanted & hosts:
                refs.append(str(record["ref"]))
        if not refs:
            raise ProvisioningError(
                f"no reservation on record covers {', '.join(sorted(wanted))}; "
                f"refusing to guess which one to cancel. Check "
                f"{self.ledger.path}."
            )
        for ref in refs:
            self.release_ref(ref)
