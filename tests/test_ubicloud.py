"""Ubicloud provisioning, exercised against a fake `ubi` CLI.

These tests never touch real infrastructure. They exist mainly to pin down
the safety properties, because the failure mode here -- destroying a VM
Yardstick did not create -- is unrecoverable:

  * a destroy is only ever issued for an identifier in the ledger;
  * the ledger entry is written before the VM is created, so a crash
    mid-create still leaves something to clean up from;
  * a failed fleet is rolled back rather than half-left;
  * nothing is ever discovered by listing or name-matching.
"""

import json
import stat
from pathlib import Path

import pytest

from yardstick_benchmark.model import Node
from yardstick_benchmark.provisioning import (
    Provisioner,
    Ubicloud,
    UbicloudError,
    UbicloudSafetyError,
)


FAKE_CLI = r"""#!/usr/bin/env python3
import json, os, sys

LOG = os.environ["FAKE_UBI_LOG"]
STATE = os.environ["FAKE_UBI_STATE"]
FAIL_ON = os.environ.get("FAKE_UBI_FAIL_ON_CREATE", "")

args = sys.argv[1:]
with open(LOG, "a") as f:
    f.write(json.dumps(args) + "\n")

state = json.load(open(STATE)) if os.path.exists(STATE) else {}

# ubi vm <ref> <command> ...
if len(args) >= 3 and args[0] == "vm":
    ref, command = args[1], args[2]
    if command == "create":
        if FAIL_ON and ref.endswith(FAIL_ON):
            sys.stderr.write("simulated create failure\n")
            sys.exit(1)
        n = len(state) + 1
        state[ref] = {
            "id": f"vm{n:026d}",
            "ip4": f"203.0.113.{n}",
            "ip6": f"2001:db8::{n}",
            "state": "running",
        }
        json.dump(state, open(STATE, "w"))
        sys.exit(0)
    if command == "destroy":
        if ref not in state:
            # also allow addressing by id
            for k, v in list(state.items()):
                if v["id"] == ref:
                    del state[k]
                    json.dump(state, open(STATE, "w"))
                    sys.exit(0)
            sys.stderr.write(f"no such vm {ref}\n")
            sys.exit(1)
        del state[ref]
        json.dump(state, open(STATE, "w"))
        sys.exit(0)
    if command == "show":
        vm = state.get(ref)
        if vm is None:
            sys.stderr.write(f"no such vm {ref}\n")
            sys.exit(1)
        fields = args[args.index("-f") + 1].split(",") if "-f" in args else []
        for field in fields:
            print(f"{field}\t{vm.get(field, '')}")
        sys.exit(0)

sys.stderr.write(f"fake ubi: unhandled {args}\n")
sys.exit(2)
"""


@pytest.fixture
def fake(tmp_path, monkeypatch):
    cli = tmp_path / "ubi"
    cli.write_text(FAKE_CLI)
    cli.chmod(cli.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("FAKE_UBI_LOG", str(tmp_path / "calls.log"))
    monkeypatch.setenv("FAKE_UBI_STATE", str(tmp_path / "state.json"))

    def make(**kwargs):
        kwargs.setdefault("ssh_public_key", "ssh-ed25519 AAAA test@example")
        kwargs.setdefault("ledger", tmp_path / "ledger.json")
        kwargs.setdefault("cli", str(cli))
        return Ubicloud(**kwargs)

    def _log():
        path = tmp_path / "calls.log"
        if not path.exists():
            return []
        return [
            json.loads(line) for line in path.read_text().splitlines() if line.strip()
        ]

    make.log = _log

    def _live():
        path = tmp_path / "state.json"
        return json.loads(path.read_text()) if path.exists() else {}

    make.live = _live
    make.ledger_path = tmp_path / "ledger.json"
    return make


def test_provision_returns_nodes_and_records_them(fake):
    cloud = fake()
    nodes = cloud.provision(2)

    assert len(nodes) == 2
    assert all(isinstance(n, Node) for n in nodes)
    assert [n.host for n in nodes] == ["203.0.113.1", "203.0.113.2"]
    assert all(str(n.wd) == "/home/ubi/yardstick" for n in nodes)

    acquired = cloud.acquired()
    assert len(acquired) == 2
    assert all(r["id"] for r in acquired), "ids must be captured for later release"


def test_the_ledger_entry_is_written_before_the_vm_is_created(fake):
    """A crash between create and recording would leak a VM, so the record
    must come first."""
    cloud = fake()
    order = []

    real_record = cloud._pre_record
    real_run = cloud._run

    def spy_record(ref, **fields):
        order.append(f"record:{ref}")
        return real_record(ref, **fields)

    def spy_run(*args, **kwargs):
        if len(args) >= 3 and args[2] == "create":
            order.append(f"create:{args[1]}")
        return real_run(*args, **kwargs)

    cloud._pre_record = spy_record
    cloud._run = spy_run
    cloud.provision(1)

    first_record = next(i for i, e in enumerate(order) if e.startswith("record:"))
    first_create = next(i for i, e in enumerate(order) if e.startswith("create:"))
    assert first_record < first_create


def test_destroy_refuses_an_id_not_in_the_ledger(fake):
    """The whole safety model: a VM Yardstick did not create is unreachable."""
    cloud = fake()
    with pytest.raises(UbicloudSafetyError, match="not in the ledger"):
        cloud.release_ref("eu-central-h1/ubi-dev-box")
    assert fake.log() == [], "nothing should have been sent to the CLI"


def test_destroy_never_lists_vms(fake):
    """A sweep would start with a list; assert we never issue one."""
    cloud = fake()
    nodes = cloud.provision(2)
    cloud.release(nodes)
    assert not any(args[:2] == ["vm", "list"] for args in fake.log()), (
        "VM discovery by listing is exactly what must never happen"
    )


def test_release_destroys_only_the_given_nodes(fake):
    cloud = fake()
    nodes = cloud.provision(3)
    cloud.release([nodes[1]])

    remaining = {r["ref"] for r in cloud.acquired()}
    assert len(remaining) == 2
    destroys = [args[1] for args in fake.log() if args[2:3] == ["destroy"]]
    assert len(destroys) == 1


def test_release_refuses_a_node_it_has_no_record_for(fake):
    cloud = fake()
    cloud.provision(1)
    stranger = Node("198.51.100.7", Path("/home/ubi/yardstick"))
    with pytest.raises(UbicloudSafetyError, match="refusing to guess"):
        cloud.release([stranger])


def test_release_all_tears_down_everything_recorded(fake):
    cloud = fake()
    cloud.provision(3)
    destroyed = cloud.release_all()
    assert len(destroyed) == 3
    assert cloud.acquired() == []
    assert fake.live() == {}


def test_a_failed_fleet_is_rolled_back(fake, monkeypatch):
    """One VM failing must not leave the others running and unaccounted for."""
    monkeypatch.setenv("FAKE_UBI_FAIL_ON_CREATE", "-2")
    cloud = fake()
    with pytest.raises(UbicloudError):
        cloud.provision(3)
    assert fake.live() == {}, "successfully created VMs must be destroyed again"
    assert cloud.acquired() == []


def test_oversized_machines_are_refused():
    for size in ("standard-30", "standard-60", "enormous"):
        with pytest.raises(UbicloudSafetyError, match="not allowed"):
            Ubicloud(size=size, ssh_public_key="x")


def test_too_many_vms_are_refused(fake):
    cloud = fake(max_vms=2)
    with pytest.raises(UbicloudSafetyError, match="the cap is 2"):
        cloud.provision(3)
    assert fake.log() == [], "nothing should reach the CLI"


def test_invalid_storage_size_is_refused():
    with pytest.raises(UbicloudSafetyError, match="storage"):
        Ubicloud(storage_gib=37, ssh_public_key="x")


def test_a_corrupt_ledger_stops_everything_rather_than_guessing(fake):
    cloud = fake()
    fake.ledger_path.write_text("{ not json")
    with pytest.raises(UbicloudError, match="corrupt"):
        cloud.acquired()


def test_missing_cli_gives_an_actionable_error(fake):
    cloud = fake(cli="/nonexistent/ubi")
    with pytest.raises(UbicloudError, match="Install the Ubicloud CLI"):
        cloud.provision(1)


def test_ledger_survives_a_new_object(fake):
    """Cleanup after a crashed run has to work from a fresh process."""
    cloud = fake()
    cloud.provision(2)
    later = fake()
    assert len(later.acquired()) == 2
    assert len(later.release_all()) == 2


def test_ubicloud_is_a_provisioner():
    assert issubclass(Ubicloud, Provisioner)
