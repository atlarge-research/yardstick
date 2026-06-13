import time
from plumbum import local
from yardstick_benchmark.model import Node
from pathlib import Path
import os


class Das(object):
    def __init__(self):
        self._reservation_map = dict()

    def _wait_for_ready(self, reservation_number: int) -> None:
        preserve = local["preserve"]
        ready = False
        while not ready:
            llist = preserve["-llist"]()
            for line in llist.split("\n")[3:]:
                parts = line.split()
                r = int(parts[0])
                if reservation_number == r:
                    ready = parts[6] == "R"
                    break
            if not ready:
                time.sleep(1)

    def _get_machines(self, reservation_number: int) -> list[str]:
        preserve = local["preserve"]
        llist = preserve["-llist"]()
        for line in llist.split("\n")[3:]:
            parts = line.split()
            r = int(parts[0])
            if reservation_number == r:
                return parts[8:]
        raise KeyError(f"reservation {reservation_number} does not exist")

    def provision(self, num=1, time_s=900) -> list[Node]:
        preserve = local["preserve"]
        reservation = int(preserve["-np", num, "-t", time_s]().split()[2][:-1])
        self._wait_for_ready(reservation)
        machines = self._get_machines(reservation)
        res = [
            Node(host=host, wd=Path(f"/local/{os.getlogin()}/yardstick/{host}"))
            for host in machines
        ]
        self._reservation_map[reservation] = set(res)
        return res

    def _cancel_reservation(self, number: int) -> None:
        preserve = local["preserve"]
        preserve["-c", number]()

    def release(self, machines: list[Node]) -> None:
        machines_to_release = set(machines)
        reservations_to_cancel = set()
        for item in self._reservation_map.items():
            item[1].difference_update(machines_to_release)
            if len(item[1]) == 0:
                reservations_to_cancel.add(item[0])
        for reservation in reservations_to_cancel:
            self._cancel_reservation(reservation)
            del self._reservation_map[reservation]
