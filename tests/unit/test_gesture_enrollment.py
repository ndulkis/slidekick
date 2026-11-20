import base64
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from slidekick.gesture_enrollment import EnrollmentSession


@pytest.fixture
def jpeg():
    success, encoded = cv2.imencode(".jpg", np.zeros((64, 64, 3), dtype=np.uint8))
    assert success
    return base64.b64encode(encoded.tobytes()).decode()


def add_all(session, root, jpeg):
    for stage_index, stage in enumerate(session.STAGES):
        result = session.add_sample(jpeg, stage, f"take_{stage_index}", root)
        assert result["status"] == "success", result


def test_all_stages_and_manifest(tmp_path, jpeg):
    session = EnrollmentSession(
        "profile_1", "enroll_1", "open_palm", target_per_stage=1
    )
    assert (
        "Expected" in session.add_sample(jpeg, "farther", "take_1", tmp_path)["error"]
    )
    add_all(session, tmp_path, jpeg)
    assert session.status == "validating"
    result = session.complete_session(tmp_path)
    manifest = json.loads(Path(result["manifest_file"]).read_text())
    assert len(manifest["samples"]) == 8
    assert len(manifest["class_manifest"]) == 1
    for sample in manifest["samples"]:
        assert sample["image_ref"].startswith("images/")
        assert "\\" not in sample["image_ref"]
        assert (tmp_path / sample["image_ref"]).is_file()
        assert (
            sample["sha256"]
            == hashlib.sha256((tmp_path / sample["image_ref"]).read_bytes()).hexdigest()
        )


def test_invalid_image_and_identifiers(tmp_path, jpeg):
    with pytest.raises(ValueError):
        EnrollmentSession("profile_1", "enroll_1", "../evil")
    session = EnrollmentSession(
        "profile_1", "enroll_1", "open_palm", target_per_stage=1
    )
    assert (
        "Invalid base64"
        in session.add_sample("%%%%", "neutral", "take_1", tmp_path)["error"]
    )
    assert (
        "Invalid capture"
        in session.add_sample(jpeg, "neutral", "../escape", tmp_path)["error"]
    )
    assert session.samples == []


def test_incomplete_session_cannot_export(tmp_path, jpeg):
    session = EnrollmentSession(
        "profile_1", "enroll_1", "open_palm", target_per_stage=1
    )
    session.add_sample(jpeg, "neutral", "take_1", tmp_path)
    assert "error" in session.complete_session(tmp_path)


def test_multiple_classes_preserved(tmp_path, jpeg):
    first_root = tmp_path / "first"
    first = EnrollmentSession("profile_1", "enroll_1", "open_palm", target_per_stage=1)
    add_all(first, first_root, jpeg)
    prior = first.complete_session(first_root)["manifest_file"]
    second_root = tmp_path / "second"
    second = EnrollmentSession("profile_1", "enroll_2", "fist", target_per_stage=1)
    add_all(second, second_root, jpeg)
    result = second.complete_session(second_root, previous_manifest=prior)
    assert result["class_count"] == 2
    assert result["total_images_saved"] == 16
    manifest = json.loads(Path(result["manifest_file"]).read_text())
    assert {x["gesture_id"] for x in manifest["class_manifest"]} == {
        "fist",
        "open_palm",
    }
    assert all((second_root / s["image_ref"]).exists() for s in manifest["samples"])


def test_integrity_rejection(tmp_path, jpeg):
    first_root = tmp_path / "first"
    first = EnrollmentSession("profile_1", "enroll_1", "open_palm", target_per_stage=1)
    add_all(first, first_root, jpeg)
    prior = Path(first.complete_session(first_root)["manifest_file"])
    manifest = json.loads(prior.read_text())
    (first_root / manifest["samples"][0]["image_ref"]).write_bytes(b"tampered")
    second_root = tmp_path / "second"
    second = EnrollmentSession("profile_1", "enroll_2", "fist", target_per_stage=1)
    add_all(second, second_root, jpeg)
    assert "Integrity mismatch" in second.complete_session(second_root, prior)["error"]
    assert second.status == "validating"
