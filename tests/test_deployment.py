"""Deployment ordering and teardown guarantees.

These use fake components, so they're fast and container-free: the point is
that a deployment never strands a running container, whatever goes wrong.
"""

import pytest

from yardstick_benchmark.deployment import Component, Deployment


class Recorder:
    """A fake component that records its lifecycle calls into a shared log."""

    def __init__(self, log, name, fail_on=None, ready=False):
        self.log = log
        self.name = name
        self.fail_on = fail_on
        self._has_ready = ready

        if ready:
            self.ready = self._ready

    def _step(self, step):
        self.log.append(f"{self.name}.{step}")
        if self.fail_on == step:
            raise RuntimeError(f"{self.name} failed during {step}")

    def deploy(self):
        self._step("deploy")

    def start(self):
        self._step("start")

    def _ready(self):
        self._step("ready")

    def stop(self):
        self._step("stop")

    def cleanup(self):
        self._step("cleanup")


def test_components_start_in_order_and_stop_in_reverse():
    log = []
    a, b = Recorder(log, "a"), Recorder(log, "b")
    with Deployment(a, b):
        log.append("body")
    assert log == [
        "a.deploy",
        "a.start",
        "b.deploy",
        "b.start",
        "body",
        "b.stop",
        "b.cleanup",
        "a.stop",
        "a.cleanup",
    ]


def test_ready_is_called_after_start_when_present():
    log = []
    with Deployment(Recorder(log, "db", ready=True)):
        pass
    assert log[:3] == ["db.deploy", "db.start", "db.ready"]


def test_ready_can_be_skipped():
    log = []
    with Deployment(Recorder(log, "db", ready=True), wait_ready=False):
        pass
    assert "db.ready" not in log


def test_failure_in_body_still_tears_everything_down():
    log = []
    a, b = Recorder(log, "a"), Recorder(log, "b")
    with pytest.raises(ValueError):
        with Deployment(a, b):
            raise ValueError("experiment blew up")
    assert log[-4:] == ["b.stop", "b.cleanup", "a.stop", "a.cleanup"]


def test_failure_during_start_tears_down_what_came_before():
    """The component that failed may still have left an instance running, so
    it must be stopped too -- not just the ones before it."""
    log = []
    a = Recorder(log, "a")
    b = Recorder(log, "b", fail_on="start")
    with pytest.raises(RuntimeError, match="b failed during start"):
        with Deployment(a, b):
            log.append("body")
    assert "body" not in log
    assert "b.stop" in log and "a.stop" in log


def test_failure_during_ready_tears_down():
    log = []
    a = Recorder(log, "a")
    b = Recorder(log, "b", ready=True, fail_on="ready")
    with pytest.raises(RuntimeError):
        with Deployment(a, b):
            pass
    assert "b.stop" in log and "a.stop" in log


def test_one_components_failed_stop_does_not_strand_the_others():
    log = []
    a = Recorder(log, "a")
    b = Recorder(log, "b", fail_on="stop")
    with pytest.raises(RuntimeError):
        with Deployment(a, b):
            pass
    # b.stop raised, but a must still have been stopped and cleaned up.
    assert "a.stop" in log and "a.cleanup" in log


def test_teardown_error_is_raised_when_the_body_succeeded():
    log = []
    with pytest.raises(RuntimeError, match="failed during stop"):
        with Deployment(Recorder(log, "a", fail_on="stop")):
            pass


def test_body_error_wins_over_teardown_error():
    """A teardown failure must not mask why the experiment actually failed."""
    log = []
    with pytest.raises(ValueError, match="real problem"):
        with Deployment(Recorder(log, "a", fail_on="stop")):
            raise ValueError("real problem")


def test_cleanup_can_be_disabled():
    log = []
    with Deployment(Recorder(log, "a"), cleanup=False):
        pass
    assert "a.stop" in log and "a.cleanup" not in log


def test_accepts_a_list_as_well_as_varargs():
    log = []
    with Deployment([Recorder(log, "a"), Recorder(log, "b")]):
        pass
    assert "a.start" in log and "b.start" in log


def test_recorder_satisfies_the_component_protocol():
    assert isinstance(Recorder([], "a"), Component)
