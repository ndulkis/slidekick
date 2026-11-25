"""S4-LOG03: Baseline verification of security logging requirements.

Expected failures document gaps identified during the interim assessment.
"""

import json
import logging
from unittest.mock import Mock, patch

import pytest

from slidekick.gesture_command_controller import GestureCommandController
from slidekick.presentation_adapter import KeyboardPresentationAdapter
from slidekick.session_coordinator import PresentationCommandError, SessionCoordinator
from windows_helper import app


def require_event(caplog, event_type):
    """Verify a structured security event and return its contents."""
    required_fields = {
        "timestamp_utc",
        "event_type",
        "component",
        "severity",
        "outcome",
    }

    for record in caplog.records:
        try:
            event = json.loads(record.getMessage())
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(event, dict):
            continue

        if event.get("event_type") != event_type:
            continue

        assert required_fields <= event.keys()
        assert isinstance(event["timestamp_utc"], str)
        assert isinstance(event["component"], str)
        assert event["severity"] in {"INFO", "WARNING", "ERROR", "CRITICAL"}
        assert event["outcome"] in {"rejected", "failed"}
        assert record.levelname == event["severity"]

        return event

    pytest.fail(f"Missing structured security event: {event_type}")


def test_t01_invalid_command_generates_security_log(caplog):
    """T01: Unsupported commands must generate rejection events."""
    adapter = KeyboardPresentationAdapter()

    with caplog.at_level(logging.DEBUG):
        result = adapter.execute_command("unsupported_command")

    assert result["status"] == "error"
    require_event(caplog, "command_rejected")


def test_t02_native_helper_failure_generates_security_log(caplog):
    """T02: Helper execution failures must produce a security event."""
    with (
        patch("windows_helper.adapter.execute_command") as execute,
        app.test_client() as client,
        caplog.at_level(logging.DEBUG),
    ):
        execute.return_value = {
            "status": "error",
            "error": "Native Execution Error",
            "command": "next",
        }
        response = client.post("/next")

    assert response.status_code == 500
    require_event(caplog, "native_execution_failed")


def test_t03_malformed_gesture_generates_security_log(caplog):
    """T03: Malformed gesture input must be observable."""
    coordinator = SessionCoordinator()
    coordinator.start()

    with caplog.at_level(logging.DEBUG):
        result = coordinator.handle_event(
            {
                "event_type": "gesture",
                "gesture": 123,
            }
        )

    assert result is False
    require_event(caplog, "malformed_event")


@pytest.mark.xfail(
    strict=True,
    reason="LOG01: raw exception messages may leak into logging",
)
def test_t05_exception_secrets_are_not_logged(caplog):
    """T05: Security logs must not expose untrusted exception text."""
    secret = "SYNTHETIC_SECRET_DO_NOT_LOG"
    malicious_text = secret + "\nFAKE_SECURITY_EVENT"

    adapter = Mock()
    adapter.next_slide.side_effect = RuntimeError(malicious_text)

    controller = GestureCommandController(adapter=adapter)
    coordinator = SessionCoordinator(gestures=controller)
    coordinator.start()

    with caplog.at_level(logging.DEBUG), pytest.raises(PresentationCommandError):
        coordinator.handle_event(
            {
                "event_type": "gesture",
                "gesture": "swipe_right",
            }
        )

    assert secret not in caplog.text
    assert "FAKE_SECURITY_EVENT" not in caplog.text
