import socket
import ipaddress
import string
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from typing import Callable, Iterable, Optional, TypeVar

from plumbum import SshMachine, local


T = TypeVar("T")


def is_localhost(host: str) -> bool:
    try:
        # Resolve hostname to all addresses
        infos = socket.getaddrinfo(host, None)
        for info in infos:
            ip = info[4][0]
            if ipaddress.ip_address(ip).is_loopback:
                return True
        return False
    except Exception:
        return False


def random_string(length: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def fan_out(
    items: Iterable[T],
    fn: Callable[[T], None],
    max_workers: Optional[int] = None,
) -> None:
    """Apply `fn` to each item in parallel via ThreadPoolExecutor. Fail-fast:
    re-raises the first exception encountered. The remaining tasks still run
    to completion in their threads, but their results are discarded.
    """
    items = list(items)
    if not items:
        return
    with ThreadPoolExecutor(max_workers=max_workers or max(1, len(items))) as pool:
        futs = [pool.submit(fn, item) for item in items]
        for fut in as_completed(futs):
            fut.result()


@contextmanager
def remote(host: str):
    """Yield a plumbum machine for `host`, closing it on exit if it's an SSH
    connection. For localhost, yields the global `local` machine which has
    no per-use lifecycle.
    """
    if is_localhost(host):
        yield local
        return
    machine = SshMachine(host)
    try:
        yield machine
    finally:
        machine.close()
