import pyautogui
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
    """MVP Adapter that uses universal keystrokes to control slides."""
    
    def next_slide(self) -> bool:
        print("Simulating: RIGHT arrow (Next Slide)")
        pyautogui.press('right')
        return True

    def previous_slide(self) -> bool:
        print("Simulating: LEFT arrow (Previous Slide)")
        pyautogui.press('left')
        return True

    def end_presentation(self) -> bool:
        print("Simulating: ESCAPE (End Presentation)")
        pyautogui.press('esc')
        return True