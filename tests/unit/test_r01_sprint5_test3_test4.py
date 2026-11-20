"""Sprint 5 R01 regression scenarios (provisional TEST-3 / TEST-4 mapping).

Confirm Jira acceptance criteria before associating these cases with ticket IDs.
"""

from slidekick.gesture_command_controller import GestureCommandController
from slidekick.gesture_profile import GestureProfile
from slidekick.session_coordinator import ProfileChangeError, SessionCoordinator


class RecordingAdapter:
    def __init__(self):
        self.commands = []

    def next_slide(self):
        self.commands.append("next")
        return True

    def previous_slide(self):
        self.commands.append("previous")
        return True

    def pause_presentation(self):
        self.commands.append("pause")
        return True

    def resume_presentation(self):
        self.commands.append("resume")
        return True


def _event():
    return {"event_type": "gesture", "gesture": "swipe_right"}


def _setup():
    adapter = RecordingAdapter()
    session = SessionCoordinator(gestures=GestureCommandController(adapter))
    first = GestureProfile(name="profile_a", bindings={"swipe_right": "next"})
    second = GestureProfile(name="profile_b", bindings={"swipe_right": "previous"})
    return session, adapter, first, second


def test_sprint5_r01_test3_paused_profile_switch_changes_executed_command():
    """A profile switch changes mappings after resume, without restarting the session."""
    session, adapter, first, second = _setup()
    session.apply_profile(first)
    session.start()
    assert session.handle_event(_event()) is True

    session.pause()
    session.apply_profile(second)
    assert session.profile_name == "profile_b"
    assert session.handle_event(_event()) is False
    session.resume()

    assert session.handle_event(_event()) is True
    assert adapter.commands == ["next", "previous"]


def test_sprint5_r01_test4_running_switch_rejected_without_changing_active_bindings():
    """Unsafe switches preserve the confirmed profile and its command mappings."""
    session, adapter, first, second = _setup()
    session.apply_profile(first)
    session.start()

    try:
        session.apply_profile(second)
    except ProfileChangeError:
        pass
    else:
        raise AssertionError("Switching while RUNNING must be rejected")

    assert session.profile_name == "profile_a"
    assert dict(session.gestures.gesture_bindings) == {"swipe_right": "next"}
    assert session.handle_event(_event()) is True
    assert adapter.commands == ["next"]
