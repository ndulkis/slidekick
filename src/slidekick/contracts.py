"""Shared event contracts for session state."""

from dataclasses import dataclass
from enum import StrEnum


class SessionState(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ENDED = "ended"


class SessionEventType(StrEnum):
    STARTED = "session_started"
    PAUSED = "session_paused"
    RESUMED = "session_resumed"
    ENDED = "session_ended"


@dataclass(frozen=True)
class SessionEvent:
    type: SessionEventType
    previous_state: SessionState
    new_state: SessionState
    use_case: str
