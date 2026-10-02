from abc import ABC, abstractmethod
from typing import Any

import pyautogui


class PresentationAdapter(ABC):
    """Abstract base class for all presentation controllers."""

    @abstractmethod
    def next_slide(self) -> bool:
        """Advance to the next slide."""
        pass

    @abstractmethod
    def previous_slide(self) -> bool:
        """Return to the previous slide."""
        pass

    @abstractmethod
    def pause_presentation(self) -> bool:
        """Pause the presentation by blanking the screen."""
        pass

    @abstractmethod
    def resume_presentation(self) -> bool:
        """Resume the presentation by removing the blank screen."""
        pass

    @abstractmethod
    def end_presentation(self) -> bool:
        """Exit presentation mode."""
        pass


class KeyboardPresentationAdapter(PresentationAdapter):
    """MVP adapter that uses universal keystrokes to control slides."""

    def next_slide(self) -> bool:
        print("Simulating: RIGHT arrow (Next Slide)")
        pyautogui.press("right")
        return True

    def previous_slide(self) -> bool:
        print("Simulating: LEFT arrow (Previous Slide)")
        pyautogui.press("left")
        return True

    def pause_presentation(self) -> bool:
        print("Simulating: B key (Pause / Black Screen)")
        pyautogui.press("b")
        return True

    def resume_presentation(self) -> bool:
        print("Simulating: B key (Resume / Restore Screen)")
        pyautogui.press("b")
        return True

    def end_presentation(self) -> bool:
        print("Simulating: ESCAPE (End Presentation)")
        pyautogui.press("esc")
        return True

    def execute_command(self, command: str) -> dict[str, Any]:
        """Validate and execute a SlideKick presentation command."""

        commands = {
            "next": self.next_slide,
            "previous": self.previous_slide,
            "pause": self.pause_presentation,
            "resume": self.resume_presentation,
        }

        normalized_command = (
            command.strip().lower() if isinstance(command, str) else ""
        )

        action = commands.get(normalized_command)

        if action is None:
            return {
                "status": "error",
                "error": "Invalid Command",
                "command": command,
            }

        try:
            action()
        except Exception as exc:
            return {
                "status": "error",
                "error": "Native Execution Error",
                "command": normalized_command,
                "message": str(exc),
            }

        return {
            "status": "success",
            "command": normalized_command,
        }