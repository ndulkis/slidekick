"""S4-R03-T1 prototype, refactored for S5-R03-T2 reusable training."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from dataset_validator import validate_dataset
from partition_dataset import prepare_partitions
from training_config import TrainingConfig

# Measure MediaPipe Model Maker import time
import_start = perf_counter()

from mediapipe_model_maker import gesture_recognizer

report_import_time = perf_counter() - import_start
print(f"[TIMING] MediaPipe Model Maker import: {report_import_time:.2f} seconds")

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = None


@dataclass(frozen=True)
class TrainingResult:
    """Results produced by a completed custom gesture training job."""

    model_path: Path
    test_accuracy: float
    test_loss: float
    training_samples: int
    validation_samples: int
    test_samples: int
    timings: dict[str, float]


def create_training_export_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")  # noqa: UP017
    job_id = f"{timestamp}_{uuid4().hex[:8]}"

    export_dir = ROOT / "exported_models" / "jobs" / job_id
    export_dir.mkdir(parents=True, exist_ok=False)

    return export_dir


def train_model(
    dataset_dir: Path,
    export_dir: Path,
    config: TrainingConfig,
    manifest_path: Path | None = None,
) -> TrainingResult:
    total_start = perf_counter()
    timings: dict[str, float] = {}

    config.validate()

    # Validate the labeled image dataset before MediaPipe preprocessing.
    validation = validate_dataset(dataset_dir)

    print(f"Dataset classes: {validation.class_counts}")
    print(f"Total image files: {validation.total_samples}")

    # Step 1: Prepare independent partitions when a manifest is available.
    if manifest_path is not None:
        print("Preparing capture-group-aware partitions...")

        start_time = perf_counter()

        partitions = prepare_partitions(
            dataset_dir=dataset_dir,
            manifest_path=manifest_path,
            output_dir=export_dir / "partitions",
        )

        timings["splitting"] = report_duration("Capture-group partitioning", start_time)

        # Step 2: Preprocess each partition independently.
        print("Preprocessing training, validation, and test datasets...")
        start_time = perf_counter()

        def load_partition(directory: Path):
            return gesture_recognizer.Dataset.from_folder(
                dirname=str(directory),
                hparams=gesture_recognizer.HandDataPreprocessingParams(),
            )

        train_data = load_partition(partitions.train)
        validation_data = load_partition(partitions.validation)
        test_data = load_partition(partitions.test)

        # All partitions must agree on their class-to-index mapping.
        labels = list(train_data.label_names)

        if (
            list(validation_data.label_names) != labels
            or list(test_data.label_names) != labels
        ):
            raise ValueError("Dataset partitions have inconsistent label mappings")

        if set(labels) != set(validation.class_counts):
            raise ValueError("Preprocessed labels do not match source gesture classes")

        timings["preprocessing"] = report_duration("Dataset preprocessing", start_time)

    else:
        # Legacy prototype mode: individual images are split randomly.
        # These results must not be presented as independent benchmarks.
        print(
            "WARNING: No capture-group manifest provided. "
            "Using legacy image-level splitting."
        )

        print("Loading and preprocessing image dataset...")
        start_time = perf_counter()

        data = gesture_recognizer.Dataset.from_folder(
            dirname=str(dataset_dir),
            hparams=gesture_recognizer.HandDataPreprocessingParams(),
        )

        timings["preprocessing"] = report_duration("Dataset preprocessing", start_time)

        print(f"Usable samples: {len(data)}")
        print(f"Labels: {data.label_names}")

        start_time = perf_counter()

        train_data, remaining_data = data.split(0.8)
        validation_data, test_data = remaining_data.split(0.5)

        timings["splitting"] = report_duration("Dataset splitting", start_time)

    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(validation_data)}")
    print(f"Test samples: {len(test_data)}")

    if min(len(train_data), len(validation_data), len(test_data)) == 0:
        raise ValueError("Dataset too small after preprocessing")

    # Step 3: Configure training hyperparameters
    hparams = gesture_recognizer.HParams(
        learning_rate=config.learning_rate,
        batch_size=config.batch_size,
        epochs=config.epochs,
        export_dir=str(export_dir),
    )

    options = gesture_recognizer.GestureRecognizerOptions(
        hparams=hparams,
    )

    # Step 4: Train the custom gesture classifier
    print("Starting custom gesture training...")

    start_time = perf_counter()

    model = gesture_recognizer.GestureRecognizer.create(
        train_data=train_data,
        validation_data=validation_data,
        options=options,
    )

    timings["training"] = report_duration("Model training", start_time)

    # Step 5: Evaluate using unseen test samples
    print("Evaluating model...")

    start_time = perf_counter()

    loss, accuracy = model.evaluate(test_data, batch_size=1)

    timings["evaluation"] = report_duration("Model evaluation", start_time)

    print(f"Test loss: {loss}")
    print(f"Test accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")

    # Step 6: Export the trained model
    print("Exporting custom model...")

    start_time = perf_counter()

    export_dir.mkdir(parents=True, exist_ok=True)
    model.export_model()

    timings["export"] = report_duration("Model export", start_time)

    model_path = export_dir / "gesture_recognizer.task"

    print(f"Exported model: {model_path}")
    print(f"File exists: {model_path.is_file()}")

    print("Training experiment finished.")

    timings["total"] = report_duration("Total training workflow", total_start)

    if not model_path.is_file():
        raise RuntimeError(f"Model export failed: {model_path}")

    return TrainingResult(
        model_path=model_path,
        test_accuracy=float(accuracy),
        test_loss=float(loss),
        training_samples=len(train_data),
        validation_samples=len(validation_data),
        test_samples=len(test_data),
        timings=timings,
    )


def report_duration(stage: str, start_time: float) -> float:
    elapsed = perf_counter() - start_time
    print(f"[TIMING] {stage}: {elapsed:.2f} seconds")
    return elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Train a custom SlideKick gesture model."
    )

    parser.add_argument(
        "--dataset-dir",
        type=Path,
        required=True,
        help="Directory containing labeled gesture images.",
    )

    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Capture-group manifest for independent dataset splitting.",
    )

    parser.add_argument(
        "--export-dir",
        type=Path,
        default=None,
        help="New directory for exported training artifacts.",
    )

    args = parser.parse_args()

    if args.export_dir is None:
        export_dir = create_training_export_dir()
    else:
        export_dir = args.export_dir
        export_dir.mkdir(parents=True, exist_ok=False)

    print(f"Training dataset: {args.dataset_dir}")
    print(f"Training job export directory: {export_dir}")

    config = TrainingConfig()

    result = train_model(
        dataset_dir=args.dataset_dir,
        export_dir=export_dir,
        config=config,
        manifest_path=args.manifest_path,
    )

    print(f"Training result: {result}")


if __name__ == "__main__":
    main()
