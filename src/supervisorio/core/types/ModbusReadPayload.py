from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModbusReadPayload:
    cw_id: str
    weight: int
    operation_type: int
    classification: int
    reason: int
    ppm: int
    operation_id: int
    timestamp: datetime
