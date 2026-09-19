from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Node(object):
    """A machine a deployment runs components on.

    Args:
        host: Address to reach the machine on.
        wd: Working directory Yardstick may use on it.
        user: Login user for SSH. None means "whoever is running Yardstick",
            which is right on a cluster where the accounts match, but not for
            a provisioned VM whose login user is set by the image (Ubicloud's
            is `ubi`).
    """

    host: str
    wd: Path
    user: Optional[str] = None
