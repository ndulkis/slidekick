import json
import os

from slidekick.gesture_enrollment import EnrollmentSession


def test_enrollment_session_creation():
    """Verify session initializes with correct default states."""
    session = EnrollmentSession(gesture_name="swipe_right", target_samples=5)
    assert session.gesture_name == "swipe_right"
    assert session.target_samples == 5
    assert session.status == "collecting"
    assert len(session.samples) == 0


def test_add_valid_sample():
    """Verify adding samples increments the count and triggers validation state."""
    session = EnrollmentSession(gesture_name="peace_sign", target_samples=2)
    response = session.add_sample([{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}])

    assert response["status"] == "success"
    assert response["current_count"] == 1
    assert session.status == "collecting"

    # Add second sample to hit the target
    response2 = session.add_sample([{"x": 0.5, "y": 0.6}])
    assert response2["current_count"] == 2
    assert session.status == "validating"


def test_add_invalid_sample():
    """Verify empty or invalid samples are rejected."""
    session = EnrollmentSession(gesture_name="fist")
    response = session.add_sample([])
    assert "error" in response


def test_cancel_session():
    """Verify cancellation clears samples and updates status."""
    session = EnrollmentSession(gesture_name="thumbs_up")
    session.add_sample([{"x": 0.1, "y": 0.2}])
    response = session.cancel_session()

    assert response["status"] == "cancelled"
    assert session.status == "cancelled"
    assert len(session.samples) == 0


def test_complete_session(tmp_path):
    """Verify completing a session saves a formatted JSON dataset."""
    # tmp_path is a built-in pytest fixture that creates a safe temporary directory for testing
    session = EnrollmentSession(gesture_name="swipe_left", target_samples=1)
    session.add_sample([{"x": 0.5, "y": 0.5}])

    storage_dir = str(tmp_path / "dataset")
    response = session.complete_session(storage_dir=storage_dir)

    assert response["status"] == "success"
    assert session.status == "completed"

    # Verify the JSON file was actually created and contains the right gesture name
    assert os.path.exists(response["file"])
    with open(response["file"], "r") as f:
        data = json.load(f)
        assert data["gesture_name"] == "swipe_left"
        assert data["sample_count"] == 1
