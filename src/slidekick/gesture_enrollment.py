"""Guided gesture enrollment and portable image-dataset manifest export.

R04 validates transport and file integrity; R03 owns landmark/pose validation.
The manifest is a *candidate* dataset, not proof the images were ML-accepted.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import uuid4

import cv2
import numpy as np

_IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_MAX_IMAGE_BYTES = 8 * 1024 * 1024
_MAX_IMAGE_DIMENSION = 4096


class EnrollmentSession:
    """Collect staged JPEGs. R03 decides ML acceptance and split eligibility."""

    STAGES = (
        "neutral",
        "slight left tilt",
        "slight right tilt",
        "closer",
        "farther",
        "reposition",
        "reform",
        "final confirmation",
    )

    def __init__(
        self,
        profile_id: str,
        enrollment_id: str,
        gesture_name: str,
        target_per_stage: int = 8,
    ) -> None:
        for label, value in (
            ("profile_id", profile_id),
            ("enrollment_id", enrollment_id),
            ("gesture_name", gesture_name),
        ):
            if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
                raise ValueError(f"{label} must be a lowercase safe identifier")
        if (
            isinstance(target_per_stage, bool)
            or not isinstance(target_per_stage, int)
            or target_per_stage < 1
        ):
            raise ValueError("target_per_stage must be a positive integer")
        self.profile_id = profile_id
        self.enrollment_id = enrollment_id
        self.gesture_name = gesture_name
        self.status = "collecting"
        self.samples: list[dict] = []
        self.target_per_stage = target_per_stage
        self.current_stage_index = 0
        self._dataset_root: Path | None = None

    @property
    def current_stage(self) -> str | None:
        return (
            self.STAGES[self.current_stage_index]
            if self.current_stage_index < len(self.STAGES)
            else None
        )

    def add_sample(
        self,
        base64_image: str,
        guided_stage_id: str,
        capture_group_id: str,
        output_dir: str | Path,
    ) -> dict:
        if self.status != "collecting":
            return {"error": "Session is not collecting."}
        if guided_stage_id != self.current_stage:
            return {"error": f"Expected guided stage: {self.current_stage}"}
        if not isinstance(capture_group_id, str) or not _IDENTIFIER.fullmatch(
            capture_group_id
        ):
            return {"error": "Invalid capture_group_id"}
        # A capture group represents one independent take, and cannot be
        # reused for another guided stage.
        if any(
            sample["capture_group_id"] == capture_group_id
            and sample["guided_stage_id"] != guided_stage_id
            for sample in self.samples
        ):
            return {"error": "Capture group already belongs to another stage"}
        root = Path(output_dir).resolve()
        if self._dataset_root is not None and self._dataset_root != root:
            return {"error": "Enrollment must use one dataset output directory"}
        if not isinstance(base64_image, str):
            return {"error": "Image must be a base64 string"}
        if base64_image.startswith("data:"):
            header, separator, data = base64_image.partition(",")
            if not separator or header.lower() not in (
                "data:image/jpeg;base64",
                "data:image/jpg;base64",
            ):
                return {"error": "Only base64 JPEG images are supported"}
        else:
            data = base64_image
        try:
            image_bytes = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError):
            return {"error": "Invalid base64 image"}
        if not image_bytes or len(image_bytes) > _MAX_IMAGE_BYTES:
            return {"error": "Image is empty or exceeds 8 MiB"}
        if not (
            image_bytes.startswith(b"\xff\xd8\xff")
            and image_bytes.endswith(b"\xff\xd9")
        ):
            return {"error": "Image is not a complete JPEG"}
        try:
            frame = cv2.imdecode(
                np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR
            )
        except cv2.error:
            frame = None
        if frame is None:
            return {"error": "JPEG could not be decoded"}
        height, width = frame.shape[:2]
        if not (
            32 <= height <= _MAX_IMAGE_DIMENSION and 32 <= width <= _MAX_IMAGE_DIMENSION
        ):
            return {"error": "JPEG dimensions are outside supported range"}

        sample_id = f"{self.gesture_name}_{uuid4().hex}"
        ref = PurePosixPath("images", self.gesture_name, f"{sample_id}.jpg")
        path = root.joinpath(*ref.parts)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as handle:
                handle.write(image_bytes)
        except OSError:
            return {"error": "Unable to save image"}
        self._dataset_root = root
        record = {
            "sample_id": sample_id,
            "gesture_id": self.gesture_name,
            "image_ref": ref.as_posix(),
            "capture_group_id": capture_group_id,
            "guided_stage_id": guided_stage_id,
            "captured_at": datetime.now(UTC).isoformat(),
            "mirrored": True,
            "sha256": hashlib.sha256(image_bytes).hexdigest(),
            "size_bytes": len(image_bytes),
            "width": width,
            "height": height,
            # A saved JPEG is not yet a usable landmark sample.
            "validation_status": "transport_valid",
        }
        self.samples.append(record)
        stage_count = sum(s["guided_stage_id"] == guided_stage_id for s in self.samples)
        if stage_count >= self.target_per_stage:
            self.current_stage_index += 1
            if self.current_stage_index == len(self.STAGES):
                self.status = "validating"
        return {
            "status": "success",
            "sample_id": sample_id,
            "current_stage": guided_stage_id,
            "stage_count": stage_count,
            "next_stage": self.current_stage,
            "validation_status": "transport_valid",
        }

    @staticmethod
    def _safe_ref(ref: object) -> PurePosixPath:
        if not isinstance(ref, str) or "\\" in ref:
            raise ValueError("image_ref must be a POSIX relative path")
        parsed = PurePosixPath(ref)
        if (
            parsed.is_absolute()
            or ".." in parsed.parts
            or ":" in ref
            or not ref.startswith("images/")
        ):
            raise ValueError("image_ref must be within images/ and relative")
        return parsed

    def complete_session(
        self,
        storage_dir: str | Path,
        previous_manifest: str | Path | None = None,
    ) -> dict:
        """Write a portable combined-class manifest.

        previous_manifest, if provided, must be from the same profile. Existing
        sample assets are copied into the new dataset root and rehashed.
        """
        if self.status != "validating":
            return {"error": "Collect every guided stage before completing"}
        root = Path(storage_dir).resolve()
        if self._dataset_root != root:
            return {"error": "Manifest must be stored at the image dataset root"}
        all_samples = list(self.samples)
        classes: list[dict] = []
        copied_paths: list[Path] = []
        try:
            if previous_manifest is not None:
                previous_path = Path(previous_manifest).resolve()
                previous = json.loads(previous_path.read_text(encoding="utf-8"))
                if previous.get("profile_id") != self.profile_id:
                    raise ValueError("Previous manifest is for another profile")
                old_classes = previous.get("class_manifest")
                old_samples = previous.get("samples")
                if not isinstance(old_classes, list) or not isinstance(
                    old_samples, list
                ):
                    raise ValueError(
                        "Previous manifest needs class_manifest and samples arrays"
                    )
                classes = [dict(c) for c in old_classes]
                if any(c.get("gesture_id") == self.gesture_name for c in classes):
                    raise ValueError(
                        "Gesture already enrolled; update/replacement not supported"
                    )
                for sample in old_samples:
                    source_ref = self._safe_ref(sample.get("image_ref"))
                    source = previous_path.parent.joinpath(*source_ref.parts).resolve()
                    if not source.is_relative_to(previous_path.parent):
                        raise ValueError("Previous sample escaped dataset root")
                    content = source.read_bytes()
                    digest = hashlib.sha256(content).hexdigest()
                    if sample.get("sha256") and sample["sha256"] != digest:
                        raise ValueError(f"Integrity mismatch for {source_ref}")
                    target = root.joinpath(*source_ref.parts)
                    if not target.resolve().is_relative_to(root):
                        raise ValueError("Destination sample escaped dataset root")
                    if target != source:
                        if target.exists():
                            if (
                                hashlib.sha256(target.read_bytes()).hexdigest()
                                != digest
                            ):
                                raise ValueError(
                                    f"Conflicting existing asset: {source_ref}"
                                )
                        else:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(source, target)
                            copied_paths.append(target)
                    enriched = dict(sample)
                    enriched["sha256"] = digest
                    enriched["size_bytes"] = len(content)
                    all_samples.append(enriched)
            known_gestures = {c.get("gesture_id") for c in classes}
            if any(
                s.get("gesture_id") not in known_gestures
                for s in all_samples[len(self.samples) :]
            ):
                raise ValueError("Previous sample does not belong to a prior class")
            ids = [s["sample_id"] for s in all_samples]
            if len(set(ids)) != len(ids):
                raise ValueError("Duplicate sample IDs in combined dataset")
            labels = [c.get("class_label") for c in classes] + [self.gesture_name]
            if len(set(labels)) != len(labels):
                raise ValueError("Duplicate class labels in combined dataset")
            classes.append(
                {
                    "gesture_id": self.gesture_name,
                    "class_label": self.gesture_name,
                    "display_name": self.gesture_name.replace("_", " ").title(),
                    "sample_ids": [s["sample_id"] for s in self.samples],
                }
            )
            manifest = {
                "schema_version": "1.0",
                "dataset_version": "1.0",
                "profile_id": self.profile_id,
                "enrollment_id": self.enrollment_id,
                "created_at": datetime.now(UTC).isoformat(),
                "asset_integrity_algorithm": "sha256",
                "class_manifest": classes,
                "samples": all_samples,
            }
            root.mkdir(parents=True, exist_ok=True)
            manifest_path = root / f"{self.enrollment_id}_manifest.json"
            if manifest_path.exists():
                raise ValueError("Manifest file already exists")
            temporary = root / f".{self.enrollment_id}_{uuid4().hex}.tmp"
            try:
                temporary.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                # Atomic rename ensures readers do not see partial JSON.
                temporary.replace(manifest_path)
            finally:
                temporary.unlink(missing_ok=True)
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
            for copied in copied_paths:
                copied.unlink(missing_ok=True)
            return {"error": f"Cannot export manifest: {exc}"}
        self.status = "completed"
        return {
            "status": "success",
            "manifest_file": str(manifest_path),
            "total_images_saved": len(all_samples),
            "class_count": len(classes),
        }

    def cancel_session(self) -> dict:
        if self.status == "completed":
            return {"error": "Completed enrollment cannot be cancelled"}
        self.status = "cancelled"
        # Do not silently delete files; caller owns data retention/cleanup.
        return {"status": "cancelled"}
