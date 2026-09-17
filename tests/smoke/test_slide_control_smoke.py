"""End-to-end smoke tests for slide control.

Keep these fast and deterministic: no webcam, display, or model training.
As gesture recognition lands, add checks here that the model loads, a
prerecorded sample produces a well-formed gesture result, and that result
maps to the right adapter command.
"""

from unittest import mock


def test_presentation_session_sends_expected_keys(adapters, fake_pyautogui):
    adapter = adapters.KeyboardPresentationAdapter()
    assert isinstance(adapter, adapters.PresentationAdapter)

    session = [
        adapter.next_slide,
        adapter.next_slide,
        adapter.previous_slide,
        adapter.end_presentation,
    ]
    assert all(command() for command in session)

    assert fake_pyautogui.press.call_args_list == [
        mock.call("right"),
        mock.call("right"),
        mock.call("left"),
        mock.call("esc"),
    ]
