from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from .command_policy import is_profile_bindable, validate_gesture_bindings
from .presentation_adapter import (
    KeyboardPresentationAdapter,
    PresentationAdapter,
)

# Default gesture bindings for the current SlideKick prototype.
# Recognition identifies the gesture; this layer decides what the gesture does.
DEFAULT_GESTURE_BINDINGS = MappingProxyType(
    {
        "swipe_right": "next",
        "swipe_left": "previous",
    }
)


class GestureCommandController:
    """Maps recognition events to presentation commands.

    Bindings are validated against command_policy before they are accepted, so an
    unapproved mapping never becomes active. Dispatch checks the policy again.
    """

    def __init__(
        self,
        adapter: PresentationAdapter | None = None,
        gesture_bindings: Mapping[str, str] | None = None,
    ) -> None:
        self.adapter = adapter or KeyboardPresentationAdapter()

        if gesture_bindings is None:
            gesture_bindings = DEFAULT_GESTURE_BINDINGS

        self._gesture_bindings = validate_gesture_bindings(gesture_bindings)

    @property
    def gesture_bindings(self) -> Mapping[str, str]:
        """Read-only view of the active bindings. Change them with set_gesture_bindings."""
        return MappingProxyType(self._gesture_bindings)

    def set_gesture_bindings(self, gesture_bindings: Mapping[str, str]) -> None:
        """Validate and replace all bindings at once.

        If validation fails the previous bindings stay active.
        """
        self._gesture_bindings = validate_gesture_bindings(gesture_bindings)

    def handle_event(self, event: dict[str, Any]) -> bool:
        """Handle an event emitted by the recognition pipeline."""

        # The camera also emits landmark events.
        # Only gesture events should trigger presentation commands.
        if event.get("event_type") != "gesture":
            return False

        gesture = event.get("gesture")

        if not isinstance(gesture, str):
            return False

        command = self._gesture_bindings.get(gesture)

        # Unknown/unbound gestures should not trigger presentation actions.
        if command is None:
            return False

        return self._execute_command(command)

    def _execute_command(self, command: str) -> bool:
        # Fail closed: only bindable commands can reach the adapter, even if the
        # bindings were changed behind validation's back.
        if not is_profile_bindable(command):
            return False

        commands = {
            "next": self.adapter.next_slide,
            "previous": self.adapter.previous_slide,
            "pause": self.adapter.pause_presentation,
            "resume": self.adapter.resume_presentation,
        }

        action = commands.get(command)

        if action is None:
            return False

        return action()
