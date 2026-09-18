from dataclasses import dataclass
from enum import Enum

from slidekick.presentation_adapter import (
    KeyboardPresentationAdapter,
    PresentationAdapter,
)


class GestureType(str, Enum):
    """Placeholder gesture vocabulary until real recognition lands."""

    NEXT = "next"
    PREVIOUS = "previous"
    END = "end"


@dataclass
class RecognitionEvent:
    """Placeholder for what the ML recognition layer will eventually emit."""

    gesture: GestureType


class PresentationController:
    """Routes recognition events to the active presentation adapter."""

    def __init__(self, adapter: PresentationAdapter | None = None) -> None:
        self.adapter = adapter or KeyboardPresentationAdapter()

    def handle_event(self, event: RecognitionEvent) -> bool:
        if event.gesture == GestureType.NEXT:
            return self.adapter.next_slide()
        if event.gesture == GestureType.PREVIOUS:
            return self.adapter.previous_slide()
        if event.gesture == GestureType.END:
            return self.adapter.end_presentation()
        return False