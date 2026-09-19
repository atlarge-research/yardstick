"""Integration tests: DAS node provisioning via the ``preserve`` reservation
tool.

These tests reserve and release real nodes on a DAS cluster through
``preserve``. They are slow and consume cluster resources, so they are marked
``slow`` and skipped automatically when ``preserve`` is not on PATH (i.e. when
not running on a DAS head node).

Run with::

    pytest -m slow tests/test_provisioning.py -s
"""

import shutil
import time

import pytest
from plumbum import local

from yardstick_benchmark.model import Node
from yardstick_benchmark.provisioning import Das


PRESERVE_PATH = shutil.which("preserve")

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(PRESERVE_PATH is None, reason="preserve not on PATH"),
]

# Keep leases short: the tests only need nodes long enough to inspect the
# reservation, and a short lease limits the blast radius if cleanup is skipped.
RESERVATION_TIME_S = 60


def _active_reservation_numbers() -> set[int]:
    """Reservation numbers currently visible to ``preserve -llist``.

    Mirrors the parsing in :class:`Das` (header is the first three lines, the
    reservation number is the first field).
    """
    llist = local["preserve"]["-llist"]()
    numbers = set()
    for line in llist.split("\n")[3:]:
        parts = line.split()
        if parts:
            numbers.add(int(parts[0]))
    return numbers


def _wait_until_reservation_gone(reservation: int, timeout_s: int = 30) -> None:
    """Block until ``preserve`` no longer lists ``reservation`` (cancellation
    is not always reflected immediately)."""
    deadline = time.monotonic() + timeout_s
    while reservation in _active_reservation_numbers():
        if time.monotonic() > deadline:
            raise AssertionError(
                f"reservation {reservation} still active after {timeout_s}s"
            )
        time.sleep(1)


@pytest.fixture
def das():
    """Yields a fresh :class:`Das` and releases any reservations it still holds
    on teardown, so a test that fails mid-way can't leak cluster nodes."""
    d = Das()
    yield d
    leftover = [node for nodes in d._reservation_map.values() for node in nodes]
    if leftover:
        d.release(leftover)


def test_provision_returns_requested_node_count(das):
    nodes = das.provision(num=1, time_s=RESERVATION_TIME_S)

    assert len(nodes) == 1
    node = nodes[0]
    assert isinstance(node, Node)
    assert node.host
    # provision() roots each node's working dir at the host name.
    assert node.wd.name == node.host


def test_provisioned_reservation_is_active(das):
    das.provision(num=1, time_s=RESERVATION_TIME_S)

    # Das records the reservation it created...
    assert len(das._reservation_map) == 1
    reservation = next(iter(das._reservation_map))
    # ...and preserve itself should report it as an active reservation.
    assert reservation in _active_reservation_numbers()


def test_release_cancels_reservation(das):
    nodes = das.provision(num=1, time_s=RESERVATION_TIME_S)
    reservation = next(iter(das._reservation_map))

    das.release(nodes)

    # Released nodes empty the reservation, which Das then cancels and forgets.
    assert reservation not in das._reservation_map
    _wait_until_reservation_gone(reservation)


def test_provision_multiple_returns_distinct_hosts(das):
    nodes = das.provision(num=2, time_s=RESERVATION_TIME_S)

    assert len(nodes) == 2
    hosts = {node.host for node in nodes}
    assert len(hosts) == 2, f"expected distinct hosts, got {hosts}"
