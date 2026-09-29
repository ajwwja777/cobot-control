"""Passive TX health: receiving CAN feedback does not prove commands can leave."""
import json
import subprocess
import time
import threading
from pathlib import Path


def read_queues(buses):
    result = {}
    payload = json.loads(subprocess.check_output(
        ["tc", "-s", "-j", "qdisc", "show"], timeout=1.0, text=True))
    for bus in buses:
        rows = [row for row in payload if row.get("dev") == bus and row.get("root")]
        if len(rows) != 1:
            continue
        root = Path("/sys/class/net") / bus
        row = rows[0]
        result[bus] = dict(
            tx_packets=int((root / "statistics/tx_packets").read_text()),
            ifindex=int((root / "ifindex").read_text()),
            queued=int(row.get("qlen", 0)), drops=int(row.get("drops", 0)))
    return result


class CanTxMonitor:
    """Confirm a non-draining queue, never transmit or reset a CAN interface."""
    def __init__(self, reader=read_queues, clock=time.monotonic):
        self.reader, self.clock, self.previous = reader, clock, {}
        self.lock = threading.Lock()

    def sample(self, buses):
        with self.lock:
            return self._sample(buses)

    def _sample(self, buses):
        now = self.clock()
        try:
            samples = self.reader(buses)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            self.previous.clear()
            return {bus:dict(phase="unknown", detail=str(exc)[:160]) for bus in buses}
        values = {}
        for bus in buses:
            sample = samples.get(bus)
            if sample is None:
                self.previous.pop(bus, None)
                values[bus] = dict(phase="unknown", detail="TX queue unavailable")
                continue
            identity = (sample["ifindex"], sample["tx_packets"])
            previous = self.previous.get(bus)
            since = now
            if sample["queued"] and previous and previous[:2] == identity:
                since = previous[2]
            # An idle, empty queue and advancing TX counters are both healthy.
            self.previous[bus] = (*identity, since) if sample["queued"] else None
            stalled = bool(sample["queued"] and now - since >= 1.0)
            values[bus] = dict(sample, phase="error" if stalled else
                               ("checking" if sample["queued"] else "ready"),
                               stalled_seconds=round(now-since, 2),
                               detail="{}: TX {}, queued {}, drops {}, no progress {:.1f}s".format(
                                   bus, sample["tx_packets"], sample["queued"], sample["drops"], now-since))
        return values
