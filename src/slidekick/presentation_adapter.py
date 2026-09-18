from abc import ABC, abstractmethod


class PresentationAdapter(ABC):
    """Abstract base class for all presentation controllers."""

    @abstractmethod
    def next_slide(self) -> bool:
        pass

    @abstractmethod
    def previous_slide(self) -> bool:
        pass

    @abstractmethod
    def end_presentation(self) -> bool:
        pass


class KeyboardPresentationAdapter(PresentationAdapter):
    """MVP Adapter that uses universal keystrokes to control slides.

    pyautogui is imported lazily inside each method rather than at module
    load time, since it requires a real display and would break importing
    this module inside the headless dev container.
    """

    def next_slide(self) -> bool:
        import pyautogui

        print("Simulating: RIGHT arrow (Next Slide)")
        pyautogui.press("right")
        return True

    def previous_slide(self) -> bool:
        import pyautogui

        print("Simulating: LEFT arrow (Previous Slide)")
        pyautogui.press("left")
        return True

    def end_presentation(self) -> bool:
        import pyautogui

        print("Simulating: ESCAPE (End Presentation)")
        pyautogui.press("esc")
        return True