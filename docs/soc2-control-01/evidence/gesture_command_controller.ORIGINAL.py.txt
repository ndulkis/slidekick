from collections.abc import Mapping
from typing import Any

from .presentation_adapter import (
    KeyboardPresentationAdapter,
    PresentationAdapter,
)

# Default gesture bindings for the current SlideKick prototype.
# Recognition identifies the gesture; this layer decides what the gesture does.
DEFAULT_GESTURE_BINDINGS = {
    "swipe_right": "next",
    "swipe_left": "previous",
}


class GestureCommandController:
    """Maps recognition events to presentation commands."""

    def __init__(
        self,
        adapter: PresentationAdapter | None = None,
        gesture_bindings: Mapping[str, str] | None = None,
    ) -> None:
        self.adapter = adapter or KeyboardPresentationAdapter()

        if gesture_bindings is None:
            self.gesture_bindings = dict(DEFAULT_GESTURE_BINDINGS)
        else:
            self.gesture_bindings = dict(gesture_bindings)

    def handle_event(self, event: dict[str, Any]) -> bool:
        """Handle an event emitted by the recognition pipeline."""

        # The camera also emits landmark events.
        # Only gesture events should trigger presentation commands.
        if event.get("event_type") != "gesture":
            return False

        gesture = event.get("gesture")

        if not isinstance(gesture, str):
            return False

        command = self.gesture_bindings.get(gesture)

        # Unknown/unbound gestures should not trigger presentation actions.
        if command is None:
            return False

        return self._execute_command(command)

    def _execute_command(self, command: str) -> bool:
        commands = {
            "next": self.adapter.next_slide,
            "previous": self.adapter.previous_slide,
            "pause": self.adapter.pause_presentation,
            "resume": self.adapter.resume_presentation,
            "end": self.adapter.end_presentation,
        }

        action = commands.get(command)

        if action is None:
            return False

        return action()
