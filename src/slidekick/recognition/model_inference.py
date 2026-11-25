"""Evaluate a trained MediaPipe gesture model using labeled images."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image

from .model_evaluation import (
    EvaluationResult,
    PredictionSample,
    evaluate_predictions,
)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class EvaluatedCandidate:
    """Evaluation results associated with a specific model artifact."""

    model_sha256: str
    evaluation: EvaluationResult


def calculate_model_hash(model_path: Path) -> str:
    """Calculate a SHA-256 fingerprint of a model artifact."""

    if not model_path.is_file():
        raise ValueError(f"Candidate model not found: {model_path}")

    digest = sha256()

    with model_path.open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def evaluate_candidate_model(
    model_path: Path,
    evaluation_dir: Path,
    labels: list[str],
) -> EvaluatedCandidate:
    """Evaluate a model and associate its results with its fingerprint."""

    before_hash = calculate_model_hash(model_path)

    evaluation = evaluate_model(
        model_path=model_path,
        evaluation_dir=evaluation_dir,
        labels=labels,
    )

    after_hash = calculate_model_hash(model_path)

    if before_hash != after_hash:
        raise RuntimeError("Candidate model changed during evaluation")

    return EvaluatedCandidate(
        model_sha256=after_hash,
        evaluation=evaluation,
    )


def evaluate_model(
    model_path: Path,
    evaluation_dir: Path,
    labels: list[str],
) -> EvaluationResult:
    """Run candidate-model inference on a labeled evaluation dataset."""

    if not model_path.is_file():
        raise ValueError(f"Candidate model not found: {model_path}")

    if not evaluation_dir.is_dir():
        raise ValueError(f"Evaluation directory not found: {evaluation_dir}")

    if not labels or len(labels) != len(set(labels)):
        raise ValueError("Evaluation labels must be nonempty and unique")

    if any(not label for label in labels):
        raise ValueError("Evaluation labels cannot contain empty strings")

    samples: list[PredictionSample] = []

    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(model_path.resolve()),
        ),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_hands=1,
    )

    with mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
        for expected in labels:
            class_dir = evaluation_dir / expected

            if not class_dir.is_dir():
                raise ValueError(f"Missing evaluation class: {expected}")

            image_paths = sorted(
                path
                for path in class_dir.iterdir()
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
            )

            for image_path in image_paths:
                with Image.open(image_path) as image:
                    rgb = np.asarray(image.convert("RGB"))

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=np.ascontiguousarray(rgb),
                )

                result = recognizer.recognize(mp_image)

                predicted = "none"

                if result.gestures and result.gestures[0]:
                    predicted = result.gestures[0][0].category_name

                    if predicted == "None":
                        predicted = "none"

                samples.append(
                    PredictionSample(
                        expected=expected,
                        predicted=predicted,
                    )
                )

    return evaluate_predictions(samples, labels)
