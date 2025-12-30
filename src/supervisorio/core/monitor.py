import time
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ComponentStatus:
    status: str = "offline"  # online, offline, error
    last_heartbeat: float = field(default_factory=time.time)
    buffer_usage: int = 0
    total_processed: int = 0
    error_count: int = 0


class SystemMonitor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemMonitor, cls).__new__(cls)
            cls._instance.components = {  # type: ignore
                "worker_pesagens": ComponentStatus(),
                "worker_eventos": ComponentStatus(),
                "modbus_collector": ComponentStatus()
            }
        return cls._instance

    def update_heartbeat(self, component_name: str, buffer_size: int = 0, increment_processed: int = 0):
        if component_name in self.components:  # type: ignore
            comp = self.components[component_name]  # type: ignore
            comp.status = "online"
            comp.last_heartbeat = time.time()
            comp.buffer_usage = buffer_size
            comp.total_processed += increment_processed

    def report_error(self, component_name: str):
        if component_name in self.components:  # type: ignore
            self.components[component_name].status = "error"  # type: ignore
            self.components[component_name].error_count += 1  # type: ignore


monitor = SystemMonitor()
