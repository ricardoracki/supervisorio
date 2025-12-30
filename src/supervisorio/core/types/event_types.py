from enum import Enum


class EventTypes(Enum):
    WEIGHT_READ = 'weight_read'
    EVENT_CHANGED = 'event_changed'
    TIMEOUT_ERROR = 'timeout_error'
    RUN = 'run'
    STOP = 'stop'
    ERROR = 'error'
