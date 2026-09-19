"""The Provisioner contract, exercised with a minimal fake provider.

These cover the rules the base class exists to enforce for every provider,
so a new one gets them for free rather than having to remember them:

  * release is addressed by recorded identifier, never by pattern;
  * the record is written before the resource is created;
  * a partial failure is rolled back;
  * the ledger outlives the process that wrote it.
"""

from pathlib import Path
from typing import Any, Dict, List

import pytest

from yardstick_benchmark.model import Node
from yardstick_benchmark.provisioning import (
    Provisioner,
    ProvisioningError,
    ProvisioningSafetyError,
    ResourceLedger,
)


class FakeProvider(Provisioner):
    """Acquires numbered resources from an in-memory 'provider'."""

    LEDGER_NAME = "fake.json"

    def __init__(self, ledger, fail_at=None, live=None):
        super().__init__(ledger=ledger)
        self.fail_at = fail_at
        self.live = live if live is not None else set()
        self.calls: List[str] = []

    def _acquire(self, num: int, **kwargs: Any) -> List[Dict[str, Any]]:
        records = []
        for index in range(num):
            ref = f"res-{index}"
            self.calls.append(f"record:{ref}")
            self._pre_record(ref, host=f"10.0.0.{index}", wd="/tmp/wd")
            if self.fail_at == index:
                raise ProvisioningError(f"provider blew up on {ref}")
            self.calls.append(f"create:{ref}")
            self.live.add(ref)
            records.append({"ref": ref, "host": f"10.0.0.{index}", "wd": "/tmp/wd"})
        return records

    def _release_one(self, record: Dict[str, Any]) -> None:
        self.calls.append(f"release:{record['ref']}")
        self.live.discard(str(record["ref"]))

    def node_for(self, record: Dict[str, Any]) -> Node:
        return Node(str(record["host"]), Path(str(record["wd"])))


@pytest.fixture
def ledger_path(tmp_path):
    return tmp_path / "ledger.json"


def test_provision_returns_nodes(ledger_path):
    nodes = FakeProvider(ledger_path).provision(2)
    assert [n.host for n in nodes] == ["10.0.0.0", "10.0.0.1"]
    assert all(isinstance(n, Node) for n in nodes)


def test_the_record_is_written_before_the_resource_is_created(ledger_path):
    provider = FakeProvider(ledger_path)
    provider.provision(1)
    assert provider.calls.index("record:res-0") < provider.calls.index("create:res-0")


def test_release_refuses_an_identifier_not_in_the_ledger(ledger_path):
    """The core safety property: a resource this provisioner did not acquire
    is unreachable, whatever it is called."""
    provider = FakeProvider(ledger_path)
    with pytest.raises(ProvisioningSafetyError, match="not in the ledger"):
        provider.release_ref("somebody-elses-vm")
    assert provider.calls == []


def test_release_refuses_a_node_it_has_no_record_for(ledger_path):
    provider = FakeProvider(ledger_path)
    provider.provision(1)
    with pytest.raises(ProvisioningSafetyError, match="refusing to guess"):
        provider.release([Node("192.0.2.99", Path("/tmp/wd"))])


def test_release_only_touches_the_named_nodes(ledger_path):
    provider = FakeProvider(ledger_path)
    nodes = provider.provision(3)
    provider.release([nodes[1]])
    assert provider.live == {"res-0", "res-2"}
    assert len(provider.acquired()) == 2


def test_release_all_gives_back_everything_recorded(ledger_path):
    provider = FakeProvider(ledger_path)
    provider.provision(3)
    assert len(provider.release_all()) == 3
    assert provider.live == set()
    assert provider.acquired() == []


def test_a_partial_failure_is_rolled_back(ledger_path):
    """One resource failing must not leave the others running and
    unaccounted for."""
    provider = FakeProvider(ledger_path, fail_at=2)
    with pytest.raises(ProvisioningError):
        provider.provision(4)
    assert provider.live == set()
    assert provider.acquired() == []


def test_rollback_covers_the_resource_that_failed(ledger_path):
    """The failing call may still have created something, so it is released
    too rather than assumed absent."""
    provider = FakeProvider(ledger_path, fail_at=1)
    with pytest.raises(ProvisioningError):
        provider.provision(3)
    assert "release:res-1" in provider.calls


def test_the_ledger_survives_the_process_that_wrote_it(ledger_path):
    """Cleanup after a crashed run has to work from a fresh object."""
    live = set()
    FakeProvider(ledger_path, live=live).provision(2)
    assert live == {"res-0", "res-1"}

    recovered = FakeProvider(ledger_path, live=live)
    assert len(recovered.acquired()) == 2
    recovered.release_all()
    assert live == set()


def test_provision_rejects_a_nonsense_count(ledger_path):
    with pytest.raises(ValueError):
        FakeProvider(ledger_path).provision(0)


def test_a_corrupt_ledger_refuses_to_guess(ledger_path):
    ledger_path.write_text("{ not json at all")
    with pytest.raises(ProvisioningError, match="corrupt"):
        FakeProvider(ledger_path).acquired()


def test_ledger_writes_are_atomic(tmp_path):
    """A half-written ledger would be indistinguishable from a lost resource,
    so entries go through a temp file and a rename."""
    ledger = ResourceLedger(tmp_path / "l.json")
    ledger.record("a", host="1.2.3.4")
    ledger.record("b", host="1.2.3.5")
    assert {r["ref"] for r in ledger.records()} == {"a", "b"}
    assert not list(tmp_path.glob("*.tmp")), "temp file should not survive"
    ledger.forget("a")
    assert {r["ref"] for r in ledger.records()} == {"b"}


def test_recording_the_same_ref_twice_updates_rather_than_duplicates(tmp_path):
    ledger = ResourceLedger(tmp_path / "l.json")
    ledger.record("a", host=None)
    ledger.record("a", host="1.2.3.4")
    assert len(ledger.records()) == 1
    assert ledger.get("a")["host"] == "1.2.3.4"


def test_each_provisioner_gets_its_own_default_ledger():
    """Two providers must not share a ledger file, or one could be asked to
    release the other's resources."""
    from yardstick_benchmark.provisioning import Das, Ubicloud

    assert Das.LEDGER_NAME != Ubicloud.LEDGER_NAME
