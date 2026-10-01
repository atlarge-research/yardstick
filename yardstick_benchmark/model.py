from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Node(object):
    """A machine a deployment runs components on.

    A node can have two addresses. `host` is the control-plane address: the
    one the machine running Yardstick reaches it on, over SSH. `private_host`
    is the address it has inside its provider's private network, which is
    only meaningful to a machine on that same network -- hence `subnet`,
    which says which network that is.

    Args:
        host: Address to reach the machine on from the control plane. Always
            usable; SSH and staging use nothing else.
        wd: Working directory Yardstick may use on it.
        user: Login user for SSH. None means "whoever is running Yardstick",
            which is right on a cluster where the accounts match, but not for
            a provisioned VM whose login user is set by the image (Ubicloud's
            is `ubi`).
        private_host: Address on the machine's private network, if it has
            one. Never used on its own: only via :meth:`data_plane_host`,
            which hands it out only to a peer on the same `subnet`.
        subnet: Identifier of the private network `private_host` belongs to.
            Two nodes reach each other privately only when this matches
            exactly, so a provisioner must report it verbatim per machine
            rather than deriving it.
    """

    host: str
    wd: Path
    user: Optional[str] = None
    private_host: Optional[str] = None
    subnet: Optional[str] = None

    def data_plane_host(self, peer: "Node") -> str:
        """The address `peer` should use to reach a service on this node.

        Benchmark traffic -- players to the game server, RCON, Telegraf to
        InfluxDB -- should stay inside the datacenter: routing it out through
        the public interface and back adds latency and, worse, variance that
        lands straight in the measurements. So when this node and `peer` are
        on the same private network, that is the address they get.

        The check is deliberately strict. A private address is only handed
        out when both nodes name the same subnet, because a private address
        used from outside it does not fail cleanly -- it hangs, or reaches
        something else entirely. Anything else (no private address, no
        subnet, different subnets, `local` and `cluster` mode nodes that have
        neither) falls back to `host`, which always works.
        """
        if (
            self.private_host
            and self.subnet
            and peer.subnet
            and self.subnet == peer.subnet
        ):
            return self.private_host
        return self.host
