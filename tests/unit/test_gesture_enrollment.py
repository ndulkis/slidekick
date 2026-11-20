"""Unit tests for the Sprint 5 JPEG-based gesture enrollment backend."""

import json
import os

from slidekick.gesture_enrollment import EnrollmentSession

# A tiny, valid base64 1x1 pixel JPEG for testing
DUMMY_BASE64_JPEG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="


def test_enrollment_session_creation():
    """Verify session initializes with correct default states."""
    session = EnrollmentSession(
        profile_id="prof_123", enrollment_id="enr_456", gesture_name="peace_sign"
    )
    assert session.status == "collecting"
    assert session.gesture_name == "peace_sign"
    assert len(session.samples) == 0


def test_add_valid_sample(tmp_path):
    """Verify adding a sample saves the image and logs metadata."""
    session = EnrollmentSession(
        profile_id="prof_123", enrollment_id="enr_456", gesture_name="peace_sign"
    )

    result = session.add_sample(
        base64_image=DUMMY_BASE64_JPEG,
        guided_stage_id="neutral",
        capture_group_id="take_1",
        output_dir=str(tmp_path),
    )

    assert result["status"] == "success"
    assert result["current_stage"] == "neutral"
    assert len(session.samples) == 1

    # Verify the file was actually saved
    filepath = session.samples[0]["image_ref"]
    assert os.path.exists(filepath)


def test_add_invalid_stage(tmp_path):
    """Verify that an unsupported stage is rejected."""
    session = EnrollmentSession(
        profile_id="prof_123", enrollment_id="enr_456", gesture_name="peace_sign"
    )

    result = session.add_sample(
        base64_image=DUMMY_BASE64_JPEG,
        guided_stage_id="unsupported_stage",
        capture_group_id="take_1",
        output_dir=str(tmp_path),
    )

    assert "error" in result
    assert "Invalid stage" in result["error"]
    assert len(session.samples) == 0


def test_cancel_session():
    """Verify cancellation clears samples and updates status."""
    session = EnrollmentSession(
        profile_id="prof_123", enrollment_id="enr_456", gesture_name="thumbs_up"
    )
    session.samples = [{"dummy": "data"}]  # Inject fake data

    result = session.cancel_session()

    assert result["status"] == "cancelled"
    assert session.status == "cancelled"
    assert len(session.samples) == 0


def test_complete_session(tmp_path):
    """Verify completing a session exports the correct Dataset Manifest."""
    session = EnrollmentSession(
        profile_id="prof_123", enrollment_id="enr_456", gesture_name="peace_sign"
    )

    # Add a mock sample so it allows completion
    session.add_sample(
        base64_image=DUMMY_BASE64_JPEG,
        guided_stage_id="neutral",
        capture_group_id="take_1",
        output_dir=str(tmp_path),
    )

    # We must mock the state since we didn't hit the 64-image target
    session.status = "validating"

    result = session.complete_session(storage_dir=str(tmp_path))

    assert result["status"] == "success"
    assert session.status == "completed"

    # Verify the manifest JSON file exists and contains the right keys
    manifest_path = result["manifest_file"]
    assert os.path.exists(manifest_path)

    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        assert manifest["profile_id"] == "prof_123"
        assert manifest["class_manifest"]["gesture_id"] == "peace_sign"
        assert len(manifest["samples"]) == 1
