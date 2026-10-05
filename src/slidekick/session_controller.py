"""Session state machine for UC10 (Start), UC6 (Pause), UC7 (Resume),
and UC8 (Finalize). See docs/session-state-model.md for the full state
diagram this implements, including the valid and invalid transition
tables.

This is separate from the gesture-to-command controller (PR #10):
that one maps a recognized gesture to a presentation command, this one
owns whether a session is running at all. The two are independent
observers of each other's events, not one built on the other.
"""

from .contracts import SessionEvent, SessionEventType, SessionState
from .observer import EventPublisher, Observer


class InvalidTransitionError(Exception):
    """Raised when a session operation is attempted from a state that
    doesn't allow it. See docs/session-state-model.md for the full
    valid/invalid transition tables.
    """


class SessionController:
    def __init__(self) -> None:
        self._state = SessionState.IDLE
        self.events = EventPublisher()

    @property
    def state(self) -> SessionState:
        return self._state

    def subscribe(self, observer: Observer) -> None:
        self.events.subscribe(observer)

    def unsubscribe(self, observer: Observer) -> None:
        self.events.unsubscribe(observer)

    def start(self) -> SessionEvent:
        """UC10: Start Presentation Mode. Valid from idle (first start)
        or ended (restart, drawn directly in the state diagram).
        """
        if self.state not in (SessionState.IDLE, SessionState.ENDED):
            raise InvalidTransitionError(f"Cannot start session from {self.state}")
        return self._transition(SessionEventType.STARTED, SessionState.RUNNING, "UC10")

    def pause(self) -> SessionEvent:
        """UC6: Pause Gesture Recognition. Valid only from running."""
        if self.state is not SessionState.RUNNING:
            raise InvalidTransitionError(f"Cannot pause session from {self.state}")
        return self._transition(SessionEventType.PAUSED, SessionState.PAUSED, "UC6")

    def resume(self) -> SessionEvent:
        """UC7: Resume Gesture Recognition. Valid only from paused."""
        if self.state is not SessionState.PAUSED:
            raise InvalidTransitionError(f"Cannot resume session from {self.state}")
        return self._transition(SessionEventType.RESUMED, SessionState.RUNNING, "UC7")

    def end(self) -> SessionEvent:
        """UC8: Finalize Presentation. Valid only from running.

        The state diagram has no edge from paused directly to
        finalized, so a paused session must be resumed before it can
        be ended. This is the open question flagged in
        docs/session-state-model.md; revisit this guard if the team
        decides paused -> ended should be allowed instead.
        """
        if self.state is not SessionState.RUNNING:
            raise InvalidTransitionError(f"Cannot end session from {self.state}")
        return self._transition(SessionEventType.ENDED, SessionState.ENDED, "UC8")

    def _transition(
        self, event_type: SessionEventType, new_state: SessionState, use_case: str
    ) -> SessionEvent:
        previous_state = self.state
        self.state = new_state
        event = SessionEvent(
            type=event_type,
            previous_state=previous_state,
            new_state=new_state,
            use_case=use_case,
        )
        self.events.publish(event)
        return event
