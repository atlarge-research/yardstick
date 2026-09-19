"""Acquiring the machines a deployment runs on.

A :class:`Provisioner` turns "I need three machines" into three
:class:`~yardstick_benchmark.model.Node`s, and gives them back afterwards.
Which machines those are is the provisioner's business: a cluster scheduler
hands out nodes that already exist (:class:`~.das.Das`), a cloud provider
creates them on demand (:class:`~.ubicloud.Ubicloud`).

Writing a new one means implementing :meth:`Provisioner._acquire` and
:meth:`Provisioner._release_one`; the base class handles the parts that are
the same everywhere and are easy to get dangerously wrong:

* **Release is addressed by recorded identifier, never by pattern.** There is
  no code path that asks the provider what exists and releases the things
  whose names look right. Sweeping is how you destroy a colleague's machine.
* **Identifiers are recorded before the resource exists.** The ledger entry
  is written first, so a crash between creating something and learning its
  name still leaves a record to clean up from.
* **The ledger outlives the process.** A run that dies half way can be
  cleaned up from a fresh one, because the record is on disk rather than in
  memory.
* **A partial failure is rolled back**, so a provisioner never leaves half a
  fleet running and unaccounted for.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from yardstick_benchmark.model import Node


logger = logging.getLogger(__name__)


DEFAULT_STATE_DIR = (
    Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    / "yardstick"
)


class ProvisioningError(RuntimeError):
    """A provisioner could not acquire or release machines."""


class ProvisioningSafetyError(ProvisioningError):
    """An operation was refused because it could affect a resource this
    provisioner did not acquire."""


class ResourceLedger:
    """A durable record of the resources a provisioner acquired.

    Cleanup has to survive the process that did the acquiring: if a run is
    interrupted, something still has to know what to release. Each entry is
    keyed by `ref`, the identifier the provider addresses that resource by.
    """

    def __init__(self, path: Path):
        self.path = Path(path)

    def records(self) -> List[Dict[str, Any]]:
        if not self.path.is_file():
            return []
        try:
            data = json.loads(self.path.read_text() or "[]")
        except json.JSONDecodeError as exc:
            raise ProvisioningError(
                f"ledger {self.path} is corrupt ({exc}). Nothing will be "
                f"released from a record that cannot be read; inspect the file "
                f"and your provider's console by hand."
            ) from exc
        return data if isinstance(data, list) else []

    def _write(self, records: Sequence[Dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Write-then-rename, so an interrupted write cannot truncate the
        # record of resources that exist.
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(list(records), indent=2) + "\n")
        tmp.replace(self.path)

    def record(self, ref: str, **fields: Any) -> None:
        """Add or update the entry for `ref`."""
        records = [r for r in self.records() if r.get("ref") != ref]
        records.append({"ref": ref, **fields})
        self._write(records)

    def forget(self, ref: str) -> None:
        self._write([r for r in self.records() if r.get("ref") != ref])

    def get(self, ref: str) -> Optional[Dict[str, Any]]:
        for record in self.records():
            if record.get("ref") == ref:
                return record
        return None

    def knows(self, ref: str) -> bool:
        return self.get(ref) is not None


class Provisioner(ABC):
    """Acquires machines for a deployment and gives them back.

    Subclasses implement :meth:`_acquire` and :meth:`_release_one`. The base
    class owns the ledger, the rollback on partial failure, and the rule that
    nothing is ever released unless it is on record as having been acquired
    here.
    """

    #: File name for this provisioner's ledger, under the state directory.
    LEDGER_NAME = "provisioned.json"

    def __init__(self, ledger: Optional[Path] = None):
        self.ledger = ResourceLedger(
            Path(ledger) if ledger is not None else DEFAULT_STATE_DIR / self.LEDGER_NAME
        )

    # ------------------------------------------------------ subclass API

    @abstractmethod
    def _acquire(self, num: int, **kwargs: Any) -> List[Dict[str, Any]]:
        """Acquire `num` resources and return one record per resource.

        Each record must contain at least ``ref`` (the identifier used to
        release it later) and ``host`` (the address to reach it on).
        Implementations must call :meth:`_pre_record` for each resource
        *before* creating it, so nothing can exist without a record of how to
        release it.
        """

    @abstractmethod
    def _release_one(self, record: Dict[str, Any]) -> None:
        """Release the single resource described by `record`."""

    def _pre_record(self, ref: str, **fields: Any) -> None:
        """Note an intent to acquire `ref`, before doing so."""
        self.ledger.record(ref, **fields)

    def _rollback(self, ref: str) -> None:
        """Best-effort release of something a failed :meth:`_acquire` may or
        may not have created. Always drops the ledger entry."""
        record = self.ledger.get(ref)
        if record is not None:
            try:
                self._release_one(record)
            except Exception as exc:
                logger.info("rollback: could not release %s (%s)", ref, exc)
        self.ledger.forget(ref)

    # --------------------------------------------------------- public API

    @abstractmethod
    def node_for(self, record: Dict[str, Any]) -> Node:
        """Build the :class:`Node` a deployment uses from a ledger record."""

    def provision(self, num: int = 1, **kwargs: Any) -> List[Node]:
        """Acquire `num` machines and return them as Nodes.

        A failure part way through releases whatever was already acquired,
        rather than leaving a partial fleet behind.
        """
        if num < 1:
            raise ValueError("num must be at least 1")
        before = {r["ref"] for r in self.ledger.records()}
        try:
            records = self._acquire(num, **kwargs)
        except BaseException:
            new = [r["ref"] for r in self.ledger.records() if r["ref"] not in before]
            if new:
                logger.warning("provisioning failed; rolling back %d", len(new))
            for ref in new:
                self._rollback(ref)
            raise
        return [self.node_for(record) for record in records]

    def acquired(self) -> List[Dict[str, Any]]:
        """Every resource on record as acquired and not yet released."""
        return self.ledger.records()

    def release(self, nodes: Sequence[Node]) -> None:
        """Release the machines backing `nodes`.

        Nodes are matched to ledger records by address. A node with no record
        is left alone and reported -- never guessed at.
        """
        by_host: Dict[str, Dict[str, Any]] = {}
        for record in self.ledger.records():
            host = record.get("host")
            if host:
                by_host[str(host)] = record
        unknown = []
        for node in nodes:
            record = by_host.get(node.host)
            if record is None:
                unknown.append(node.host)
                continue
            self.release_ref(str(record["ref"]))
        if unknown:
            raise ProvisioningSafetyError(
                f"no ledger entry for {', '.join(unknown)}; refusing to guess "
                f"what to release. Use release_all() to give back everything "
                f"this provisioner acquired, or check {self.ledger.path}."
            )

    def release_ref(self, ref: str) -> None:
        """Release one resource, addressed by an identifier from the ledger.

        Refuses anything the ledger does not know about: that is the whole
        safety model, and the reason nothing here ever discovers its target by
        listing the provider.
        """
        record = self.ledger.get(ref)
        if record is None:
            raise ProvisioningSafetyError(
                f"refusing to release {ref!r}: it is not in the ledger "
                f"({self.ledger.path}), so this provisioner did not acquire "
                f"it. Release it through your provider directly if that is "
                f"really what you want."
            )
        logger.info("releasing %s", ref)
        self._release_one(record)
        self.ledger.forget(ref)

    def release_all(self) -> List[str]:
        """Release everything on record. Returns what was released.

        Still identifier-driven: it walks the records this provisioner wrote,
        not the provider's inventory.
        """
        released = []
        for record in list(self.ledger.records()):
            ref = str(record["ref"])
            try:
                self.release_ref(ref)
                released.append(ref)
            except Exception as exc:
                logger.error("could not release %s: %s", ref, exc)
        return released


from yardstick_benchmark.provisioning.das import Das  # noqa: E402
from yardstick_benchmark.provisioning.ubicloud import (  # noqa: E402
    Ubicloud,
    UbicloudError,
    UbicloudSafetyError,
)

__all__ = [
    "Das",
    "DEFAULT_STATE_DIR",
    "Provisioner",
    "ProvisioningError",
    "ProvisioningSafetyError",
    "ResourceLedger",
    "Ubicloud",
    "UbicloudError",
    "UbicloudSafetyError",
]
