"""Gate recognition events through the authoritative session state machine.

Lifecycle pause affects recognition commands, not the slideshow black-screen key.
"""

import logging
from collections.abc import Mapping
from typing import Any

from .contracts import SessionState
from .gesture_command_controller import GestureCommandController
from .session_controller import SessionController

logger = logging.getLogger(__name__)


class PresentationCommandError(RuntimeError):
    """A mapped presentation command failed to execute."""


class SessionCoordinator:
    """Connect an existing session to a gesture command controller."""

    def __init__(
        self,
        session: SessionController | None = None,
        gestures: GestureCommandController | None = None,
    ) -> None:
        self.session = session if session is not None else SessionController()
        self.gestures = gestures if gestures is not None else GestureCommandController()
        self.last_error: str | None = None

    @property
    def state(self) -> SessionState:
        return self.session.state

    def start(self) -> None:
        self.session.start()
        self.last_error = None

    def pause(self) -> None:
        self.session.pause()

    def resume(self) -> None:
        self.session.resume()

    def end(self) -> None:
        self.session.end()

    def handle_event(self, event: Mapping[str, Any] | Any) -> bool:
        """Execute only bound gestures during RUNNING; ignore malformed input."""
        if self.state is not SessionState.RUNNING or not isinstance(event, Mapping):
            return False
        if event.get("event_type") != "gesture":
            return False
        gesture = event.get("gesture")
        if not isinstance(gesture, str) or gesture not in self.gestures.gesture_bindings:
            return False
        try:
            result = self.gestures.handle_event(dict(event))
        except Exception as exc:
            self.last_error = f"Presentation command failed: {exc}"
            logger.exception(self.last_error)
            raise PresentationCommandError(self.last_error) from exc
        if result is not True:
            self.last_error = f"Presentation command was not executed for {gesture}"
            raise PresentationCommandError(self.last_error)
        self.last_error = None
        return True
