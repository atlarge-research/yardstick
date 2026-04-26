import socket
import ipaddress
import string
import random
from contextlib import contextmanager

from plumbum import SshMachine, local


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
