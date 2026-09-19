"""Composing components into a deployment.

Every Yardstick component -- a game server, a database, a metrics agent, a
workload -- follows the same four-step lifecycle:

    deploy()    put whatever the component needs onto its node
    start()     launch it
    stop()      shut it down
    cleanup()   remove what deploy() put there

:class:`Deployment` runs that lifecycle for a group of components in order,
and guarantees the teardown half runs even if something fails in the middle::

    with Deployment(influxdb, telegraf, server) as d:
        server.set_world_spawn(0, 0)
        workload.deploy()
        workload.run(health_check=server.assert_healthy)
        influxdb.export_csv(Path("results"))

Components come up in the order given and go down in reverse, so list them
in dependency order -- database before the agents that write to it, game
server before the workload that connects to it.

Anything with the four lifecycle methods can join a Deployment, so a custom
component is just a class, with no registration step:

    class MyProxy:
        def __init__(self, node): ...
        def deploy(self): ...
        def start(self): ...
        def stop(self): ...
        def cleanup(self): ...
"""

import logging
from typing import Any, List, Protocol, Sequence, runtime_checkable


logger = logging.getLogger(__name__)


@runtime_checkable
class Component(Protocol):
    """The lifecycle every deployable Yardstick component implements."""

    def deploy(self) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def cleanup(self) -> None: ...


class Deployment:
    """Bring a group of components up together, and always take them down.

    Args:
        components: Components in dependency order. They are deployed and
            started in this order, and stopped and cleaned up in reverse.
        cleanup: Whether to call cleanup() during teardown. Pass False to
            leave working directories on the nodes for inspection -- note
            that this also keeps the InfluxDB storage directory, so a later
            run can query it.
        wait_ready: Whether to call each component's ready() after start(),
            for components that define one (the game server and the database
            do). Turn it off only if you want to drive readiness yourself.
    """

    def __init__(
        self,
        *components: Any,
        cleanup: bool = True,
        wait_ready: bool = True,
    ) -> None:
        if len(components) == 1 and isinstance(components[0], (list, tuple)):
            components = tuple(components[0])
        self.components: Sequence[Any] = components
        self.do_cleanup = cleanup
        self.wait_ready = wait_ready
        self._started: List[Any] = []

    def __enter__(self) -> "Deployment":
        try:
            for component in self.components:
                name = type(component).__name__
                logger.info("deploying %s", name)
                component.deploy()
                logger.info("starting %s", name)
                # Track it *before* start() is attempted: a component that
                # failed partway through start() may still have left an
                # apptainer instance behind, and must be stopped.
                self._started.append(component)
                component.start()
                ready = getattr(component, "ready", None)
                if self.wait_ready and callable(ready):
                    logger.info("waiting for %s", name)
                    ready()
        except BaseException:
            # Never leave a half-built deployment running.
            self._teardown()
            raise
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        errors = self._teardown()
        # If the body already failed, that exception is the interesting one;
        # teardown errors are logged above. Only raise them when the body
        # succeeded, so a failed teardown can't pass silently.
        if errors and exc_type is None:
            raise errors[0]

    def _teardown(self) -> List[BaseException]:
        errors: List[BaseException] = []
        for component in reversed(self._started):
            name = type(component).__name__
            for step in ("stop", "cleanup"):
                if step == "cleanup" and not self.do_cleanup:
                    continue
                try:
                    logger.info("%s %s", step, name)
                    getattr(component, step)()
                except BaseException as exc:
                    # Keep going: one component's failure to shut down must
                    # not strand the rest of the deployment.
                    logger.warning("%s.%s() failed: %s", name, step, exc)
                    errors.append(exc)
        self._started = []
        return errors
