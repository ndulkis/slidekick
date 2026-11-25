"""Adapt R04 enrollment metadata for R03 capture-group splitting."""

from pathlib import PurePosixPath


def normalize_enrollment_sample(sample: dict) -> dict[str, str]:
    """Convert an R04 sample reference to the R03 manifest format."""

    required_fields = (
        "gesture_id",
        "image_ref",
        "capture_group_id",
        "guided_stage_id",
    )

    for field in required_fields:
        if not isinstance(sample.get(field), str) or not sample[field].strip():
            raise ValueError(f"Missing or invalid enrollment field: {field}")

    gesture_id = sample["gesture_id"]
    image_ref = sample["image_ref"]

    if "\\" in image_ref or ":" in image_ref:
        raise ValueError("Invalid enrollment image reference")

    path = PurePosixPath(image_ref)

    if (
        path.is_absolute()
        or len(path.parts) != 3
        or path.parts[0] != "images"
        or path.parts[1] != gesture_id
        or any(part in {".", ".."} for part in path.parts)
    ):
        raise ValueError("Enrollment image reference has an invalid structure")

    return {
        "gesture_id": gesture_id,
        "image_path": f"{gesture_id}/{path.name}",
        "capture_group_id": sample["capture_group_id"],
        "guided_stage_id": sample["guided_stage_id"],
    }


def normalize_enrollment_manifest(manifest: dict) -> dict:
    """Normalize all gesture classes in an R04 enrollment manifest."""

    if not isinstance(manifest, dict):
        raise TypeError("Enrollment manifest must be an object")

    classes = manifest.get("class_manifest")
    samples = manifest.get("samples")

    if not isinstance(classes, list) or not classes:
        raise ValueError("Enrollment manifest must contain gesture classes")

    if not isinstance(samples, list) or not samples:
        raise ValueError("Enrollment manifest must contain samples")

    gesture_ids = set()

    for entry in classes:
        if not isinstance(entry, dict):
            raise TypeError("Gesture class must be an object")

        gesture_id = entry.get("gesture_id")

        if not isinstance(gesture_id, str) or not gesture_id.strip():
            raise ValueError("Invalid gesture class identifier")

        if gesture_id == "none":
            raise ValueError("'none' is reserved for negative samples")

        if entry.get("class_label") != gesture_id:
            raise ValueError("Gesture class label does not match identifier")

        if gesture_id in gesture_ids:
            raise ValueError(f"Duplicate gesture class: {gesture_id}")

        gesture_ids.add(gesture_id)

    normalized_samples = []
    seen_paths = set()

    for sample in samples:
        if not isinstance(sample, dict):
            raise TypeError("Enrollment sample must be an object")

        gesture_id = sample.get("gesture_id")

        if isinstance(gesture_id, str) and gesture_id not in gesture_ids:
            raise ValueError(f"Sample references undeclared gesture: {gesture_id}")

        normalized = normalize_enrollment_sample(sample)

        image_path = normalized["image_path"]

        if image_path in seen_paths:
            raise ValueError(f"Duplicate sample image: {image_path}")

        seen_paths.add(image_path)
        normalized_samples.append(normalized)

    represented_classes = {sample["gesture_id"] for sample in normalized_samples}

    if represented_classes != gesture_ids:
        raise ValueError("Every declared gesture requires samples")

    return {"samples": normalized_samples}
