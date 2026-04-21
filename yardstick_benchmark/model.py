from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Node(object):
    host: str
    wd: Path
