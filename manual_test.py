import time

from src.slidekick.presentation_adapter import KeyboardPresentationAdapter

print("Switching slides in 3 seconds. Click into the browser!")
time.sleep(3)

adapter = KeyboardPresentationAdapter()
adapter.next_slide()
