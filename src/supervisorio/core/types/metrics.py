from datetime import datetime
from dataclasses import dataclass


@dataclass
class Metrics:

    def __init__(self):
        self.reads_total = 0
        self.reads_success = 0
        self.reads_error = 0
        self.reads_timeout = 0
        self.reconnects_total = 0
        self.last_latency: float = 0
        self.latency: float = 0
        self.connected = False
        self.started_at = datetime.now()

    @property
    def uptime(self):
        return (datetime.now() - self.started_at).total_seconds()
