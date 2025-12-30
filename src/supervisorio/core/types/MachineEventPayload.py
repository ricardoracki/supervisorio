from datetime import datetime, timedelta
from dataclasses import dataclass
from supervisorio.core.types.event_types import EventTypes


@dataclass
class MachineStopEventPayload:
    cw_id: str
    reason: int
    event_type: None | EventTypes
    ended_at: datetime | None
    started_at: datetime | None
    timestamp: timedelta | None  # duração
