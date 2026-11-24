"""Tests for converting R04 enrollment metadata to R03 training metadata."""

import importlib
from pathlib import Path

import pytest


@pytest.fixture
def adapter(monkeypatch: pytest.MonkeyPatch):
    scripts_dir = Path(__file__).resolve().parents[2] / "training" / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))

    return importlib.import_module("enrollment_manifest_adapter")


@pytest.fixture
def valid_sample() -> dict:
    return {
        "gesture_id": "pinch",
        "image_ref": "images/pinch/pinch_001.jpg",
        "capture_group_id": "session_001",
        "guided_stage_id": "neutral",
    }


def test_normalizes_enrollment_sample(adapter, valid_sample):
    result = adapter.normalize_enrollment_sample(valid_sample)

    assert result == {
        "gesture_id": "pinch",
        "image_path": "pinch/pinch_001.jpg",
        "capture_group_id": "session_001",
        "guided_stage_id": "neutral",
    }


def test_preserves_capture_group(adapter, valid_sample):
    result = adapter.normalize_enrollment_sample(valid_sample)

    assert result["capture_group_id"] == valid_sample["capture_group_id"]
    assert result["guided_stage_id"] == valid_sample["guided_stage_id"]


@pytest.mark.parametrize(
    "field",
    [
        "gesture_id",
        "image_ref",
        "capture_group_id",
        "guided_stage_id",
    ],
)
def test_rejects_missing_required_metadata(adapter, valid_sample, field):
    del valid_sample[field]

    with pytest.raises(ValueError, match="Missing or invalid"):
        adapter.normalize_enrollment_sample(valid_sample)


@pytest.mark.parametrize(
    "image_ref",
    [
        "../pinch/sample.jpg",
        "/images/pinch/sample.jpg",
        "images/other_gesture/sample.jpg",
        "images/pinch/subfolder/sample.jpg",
        "images\\pinch\\sample.jpg",
        "C:/images/pinch/sample.jpg",
    ],
)
def test_rejects_invalid_image_references(adapter, valid_sample, image_ref):
    valid_sample["image_ref"] = image_ref

    with pytest.raises(ValueError, match="Invalid|invalid"):
        adapter.normalize_enrollment_sample(valid_sample)


def test_does_not_modify_original_sample(adapter, valid_sample):
    original = valid_sample.copy()

    adapter.normalize_enrollment_sample(valid_sample)

    assert valid_sample == original


@pytest.fixture
def combined_manifest() -> dict:
    return {
        "class_manifest": [
            {"gesture_id": "pinch", "class_label": "pinch"},
            {"gesture_id": "thumbs_up", "class_label": "thumbs_up"},
        ],
        "samples": [
            {
                "gesture_id": "pinch",
                "image_ref": "images/pinch/pinch_001.jpg",
                "capture_group_id": "pinch_group_001",
                "guided_stage_id": "neutral",
            },
            {
                "gesture_id": "thumbs_up",
                "image_ref": "images/thumbs_up/thumbs_001.jpg",
                "capture_group_id": "thumbs_group_001",
                "guided_stage_id": "neutral",
            },
        ],
    }


def test_normalizes_multiple_gesture_classes(adapter, combined_manifest):
    result = adapter.normalize_enrollment_manifest(combined_manifest)

    assert len(result["samples"]) == 2

    assert {sample["gesture_id"] for sample in result["samples"]} == {
        "pinch",
        "thumbs_up",
    }

    assert result["samples"][0]["image_path"] == "pinch/pinch_001.jpg"
    assert result["samples"][1]["image_path"] == ("thumbs_up/thumbs_001.jpg")


def test_rejects_duplicate_gesture_classes(adapter, combined_manifest):
    combined_manifest["class_manifest"].append(
        {"gesture_id": "pinch", "class_label": "pinch"}
    )

    with pytest.raises(ValueError, match="Duplicate gesture class"):
        adapter.normalize_enrollment_manifest(combined_manifest)


def test_rejects_undeclared_gesture(adapter, combined_manifest):
    combined_manifest["samples"][0]["gesture_id"] = "unknown"

    with pytest.raises(ValueError, match="undeclared gesture"):
        adapter.normalize_enrollment_manifest(combined_manifest)


def test_rejects_duplicate_sample_images(adapter, combined_manifest):
    combined_manifest["samples"].append(combined_manifest["samples"][0].copy())

    with pytest.raises(ValueError, match="Duplicate sample image"):
        adapter.normalize_enrollment_manifest(combined_manifest)


def test_requires_samples_for_every_class(adapter, combined_manifest):
    combined_manifest["samples"].pop()

    with pytest.raises(ValueError, match="requires samples"):
        adapter.normalize_enrollment_manifest(combined_manifest)
