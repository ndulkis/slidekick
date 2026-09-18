from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slidekick.controller import GestureType, PresentationController, RecognitionEvent

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = PresentationController()


@app.post("/api/gesture/{gesture}")
def trigger_gesture(gesture: GestureType):
    event = RecognitionEvent(gesture=gesture)
    success = controller.handle_event(event)
    return {"success": success}
