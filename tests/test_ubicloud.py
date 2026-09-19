"""Ubicloud provisioning, exercised against a fake `ubi` CLI.

These tests never touch real infrastructure. They exist mainly to pin down
the safety properties, because the failure mode here -- destroying a VM
Yardstick did not create -- is unrecoverable:

  * a destroy is only ever issued for an identifier in the ledger;
  * the ledger entry is written before the VM is created, so a crash
    mid-create still leaves something to clean up from;
  * a failed fleet is rolled back rather than half-left;
  * nothing is ever discovered by listing or name-matching.

The fake is also pinned against recorded output from the real CLI, under
``tests/fixtures/ubi/``. A fake that encodes the same assumption as the code
under test proves nothing -- that is exactly how `ubi vm show` came to be
parsed as tab-separated while the CLI printed ``key: value``.
"""

import json
import re
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
import fcntl, json, os, sys

LOG = os.environ["FAKE_UBI_LOG"]
STATE = os.environ["FAKE_UBI_STATE"]
FAIL_ON = os.environ.get("FAKE_UBI_FAIL_ON_CREATE", "")

args = sys.argv[1:]
# Yardstick creates machines in parallel, so several copies of this script
# run at once; without a lock they clobber each other's state file.
lock = open(STATE + ".lock", "w")
fcntl.flock(lock, fcntl.LOCK_EX)

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
            # Real `ubi vm show` prints "key: value", not tab-separated.
            print(f"{field}: {vm.get(field, '')}")
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
        # No init script by default: the readiness wait it triggers would
        # try to SSH to the fake's TEST-NET addresses. The bootstrap path
        # gets its own tests below.
        kwargs.setdefault("init_script", "")
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
    # Machines are created concurrently, so which one gets which address is
    # up to the provider; only the set is predictable.
    assert {n.host for n in nodes} == {"203.0.113.1", "203.0.113.2"}
    assert all(str(n.wd) == "/home/ubi/yardstick" for n in nodes)
    assert all(n.user == "ubi" for n in nodes), "SSH needs the image's login user"

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


def test_the_init_script_is_passed_to_create(fake):
    """Ubicloud's images are bare, so a node with no apptainer fails every
    deploy() later on. The bootstrap has to actually be sent."""
    cloud = fake(init_script="#!/bin/bash\necho hi\n")
    cloud._wait_until_provisioned = lambda record, timeout_s: None
    cloud.provision(1)
    create = next(args for args in fake.log() if args[2:3] == ["create"])
    assert "-i" in create
    assert create[create.index("-i") + 1] == "#!/bin/bash\necho hi\n"


def test_no_init_script_means_no_readiness_wait(fake):
    called = []
    cloud = fake(init_script="")
    cloud._wait_until_provisioned = lambda record, timeout_s: called.append(1)
    cloud.provision(1)
    assert called == [], "nothing to wait for when no bootstrap was requested"
    create = next(args for args in fake.log() if args[2:3] == ["create"])
    assert "-i" not in create


def test_the_default_bootstrap_installs_apptainer_and_marks_readiness():
    script = Ubicloud.DEFAULT_INIT_SCRIPT
    assert "apt-get install -y apptainer" in script
    # Ubicloud reports a VM running long before apt has finished, so the
    # marker is the only reliable signal that the machine is usable.
    assert Ubicloud.READY_MARKER in script


def test_the_default_image_avoids_the_apparmor_userns_restriction():
    """Ubuntu >= 24.04 blocks unprivileged user namespaces with AppArmor,
    which is exactly what apptainer needs to run rootless."""
    assert Ubicloud.DEFAULT_BOOT_IMAGE == "ubuntu-jammy"


def test_nodes_come_back_in_the_order_they_were_requested(fake):
    """Callers index into this list -- the runner hands node i the bot_index
    i -- so concurrent creation must not shuffle the result."""
    cloud = fake()
    nodes = cloud.provision(4)
    refs = [r["ref"] for r in cloud.acquired()]
    hosts_by_ref = {r["ref"]: r["host"] for r in cloud.acquired()}
    assert [n.host for n in nodes] == [hosts_by_ref[ref] for ref in sorted(refs)]


def test_machines_are_created_concurrently(fake, monkeypatch):
    """Provisioning four machines should take about as long as one; each
    spends minutes in its init script."""
    import threading
    import time

    concurrent = []
    live = {"n": 0}
    guard = threading.Lock()
    real_create = Ubicloud._create

    def slow_create(self, ref):
        with guard:
            live["n"] += 1
            concurrent.append(live["n"])
        time.sleep(0.2)
        with guard:
            live["n"] -= 1
        return real_create(self, ref)

    monkeypatch.setattr(Ubicloud, "_create", slow_create)
    cloud = fake(max_vms=4)
    cloud.provision(4)
    assert max(concurrent) > 1, "creates ran one after another"


def test_constructing_does_not_need_an_ssh_key(tmp_path, monkeypatch):
    """`yardstick validate` constructs a provisioner to check machine sizes.
    That has to work on a machine with no SSH key -- whether a configuration
    is well-formed is a different question from whether this machine happens
    to be ready to provision. CI has no key, and this failed there."""
    monkeypatch.setenv("HOME", str(tmp_path))  # no ~/.ssh at all
    Ubicloud(size="standard-2", ledger=tmp_path / "l.json")  # must not raise


def test_a_missing_ssh_key_is_reported_when_machines_are_created(fake, monkeypatch):
    """...but it must still fail clearly, and before anything is created."""
    monkeypatch.setenv("HOME", str(fake.ledger_path.parent / "nohome"))
    cloud = fake(ssh_public_key=None)
    with pytest.raises(UbicloudError, match="no SSH public key found"):
        cloud.provision(1)
    assert fake.log() == [], "nothing should have reached the CLI"
    assert cloud.acquired() == [], "and nothing should be left on record"


def test_an_explicit_key_is_used_verbatim(fake):
    cloud = fake(ssh_public_key="ssh-ed25519 AAAAexplicit me@host")
    cloud._wait_until_provisioned = lambda record, timeout_s: None
    cloud.provision(1)
    create = next(args for args in fake.log() if args[2:3] == ["create"])
    assert create[-1] == "ssh-ed25519 AAAAexplicit me@host"


# ------------------------------------------------- the fake vs. the real CLI
#
# Everything above trusts the fake. These pin the fake, and the parser, to
# recorded output from the real `ubi`; see tests/fixtures/ubi/README.md for
# where it came from and how to re-record it.

RECORDED = Path(__file__).parent / "fixtures" / "ubi"

#: The fields Ubicloud._refresh and _wait_until_running actually ask for.
SHOW_FIELDS = ("id", "ip4", "ip6", "state")

#: One "key: value" line per field; a field with no value is a bare "key:".
REAL_SHOW_LINE = re.compile(r"[a-z0-9_]+:(?: \S.*)?")


def _show_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


@pytest.mark.parametrize("sample", ["vm_show_running", "vm_show_creating"])
def test_recorded_output_is_key_colon_value(sample):
    """Guards the fixtures themselves: if someone re-records them in a
    different shape, the assertions below would silently mean less."""
    lines = _show_lines((RECORDED / f"{sample}.txt").read_text())
    assert [line.split(":")[0] for line in lines] == list(SHOW_FIELDS)
    for line in lines:
        assert REAL_SHOW_LINE.fullmatch(line), f"unexpected line shape: {line!r}"


def test_the_parser_reads_recorded_real_output(fake):
    """The regression the fake could not catch: `state` has to come back as
    "running", not "" under a key of "state:"."""
    cloud = fake()
    cloud._run = lambda *args, **kwargs: (RECORDED / "vm_show_running.txt").read_text()

    assert cloud._show("eu-central-h1/vm", *SHOW_FIELDS) == {
        "id": "vm0j5f8z9k2m3n4p5q6r7s8t9v",
        "ip4": "203.0.113.42",
        # Split on the *first* colon only, or an address loses most of itself.
        "ip6": "2001:db8:4f2a:1::2",
        "state": "running",
    }


def test_the_parser_reads_a_field_the_cli_left_empty(fake):
    """A VM that has no IPv4 address yet prints a bare "ip4:"."""
    cloud = fake()
    cloud._run = lambda *args, **kwargs: (RECORDED / "vm_show_creating.txt").read_text()

    fields = cloud._show("eu-central-h1/vm", *SHOW_FIELDS)
    assert fields["ip4"] == ""
    assert fields["state"] == "creating"


def test_the_fake_cli_prints_what_the_real_one_prints(fake):
    """The fake is only worth anything while its output format matches.

    Compares the fake's `vm show` line-for-line in shape against the
    recording -- same fields, same order, same separator.
    """
    cloud = fake()
    cloud.provision(1)
    ref = cloud.acquired()[0]["ref"]

    produced = _show_lines(cloud._run("vm", ref, "show", "-f", ",".join(SHOW_FIELDS)))
    recorded = _show_lines((RECORDED / "vm_show_running.txt").read_text())

    assert [line.split(":")[0] for line in produced] == [
        line.split(":")[0] for line in recorded
    ]
    for line in produced:
        assert REAL_SHOW_LINE.fullmatch(line), (
            f"the fake printed {line!r}, which the real CLI would not"
        )
