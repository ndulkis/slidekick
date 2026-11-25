
# SlideKick Custom Gesture Training

## Overview

SlideKick uses MediaPipe Model Maker to train custom hand gesture recognition models from labeled images.

The training pipeline supports dataset validation, capture-group-aware splitting, model evaluation, acceptance checks, activation, and rollback.

Training uses a separate Python 3.10 environment because Model Maker's dependencies differ from those of the main SlideKick application (Python 3.11).

## Environment Setup (Windows + WSL)

Requirements:
- Windows with WSL and Ubuntu installed
- `uv` installed inside WSL
- The main SlideKick Python 3.11 environment
- Dependencies in `training/requirements.txt`

From PowerShell at the repository root:

```powershell
wsl.exe --exec bash -lc "bash training/setup_wsl.sh"
```

The script:
1. Installs or locates Python 3.10 through `uv`.
2. Creates `training/.venv` if necessary.
3. Installs the pinned training dependencies.
4. Verifies TensorFlow Metadata and MediaPipe Model Maker imports.

The environment is local and excluded from Git. The main application continues using Python 3.11.

Native Model Maker setup on macOS and other platforms has not yet been verified.

## Dataset Requirements

Model Maker expects a labeled directory structure:

```text
dataset/
├── pinch/
│   └── sample_001.jpg
└── none/
    └── sample_001.jpg
```

Each custom gesture must have its own class directory. The `none` class represents background or non-gesture examples.

For new training workflows, supply a capture-group manifest to prevent samples from the same capture group from crossing training, validation, and test partitions.

Example manifest:

```json
{
  "samples": [
    {
      "gesture_id": "pinch",
      "image_path": "pinch/sample_001.jpg",
      "capture_group_id": "pinch_take_01",
      "guided_stage_id": "neutral"
    },
    {
      "gesture_id": "none",
      "image_path": "none/sample_001.jpg",
      "capture_group_id": "background_take_01",
      "guided_stage_id": "background"
    }
  ]
}
```

Each class needs at least three distinct capture groups for grouped splitting. Real capture groups should represent independent capture takes; assigning artificial groups to related images does not establish independent evaluation.

The grouped manifest must describe every image in the prepared dataset. Keep it outside the labeled dataset directory.

### Enrollment Integration

R04's `EnrollmentSession` exports images and a completed enrollment manifest.

R03's `training/scripts/prepare_grouped_dataset.py` converts the enrollment data and a separate negative-sample manifest into Model Maker's labeled directory structure.

The preparation process preserves existing gesture classes when an enrollment manifest contains multiple gestures.

Sample storage and manifest compatibility have been tested, but a transport-valid JPEG is not automatically an ML-approved gesture sample.

## Running Training

The repository training script is:

`training/scripts/train_prototype.py`

From the repository root inside WSL, using the dedicated training environment:

```bash
training/.venv/bin/python training/scripts/train_prototype.py \
  --dataset-dir /absolute/path/to/dataset \
  --manifest-path /absolute/path/to/capture_groups.json \
  --export-dir /absolute/path/to/new-export
```

Replace the example paths with actual WSL-accessible paths, such as `/mnt/c/...` for datasets stored on Windows.

The export directory must not already exist.

The trainer:
1. Validates the labeled dataset and capture-group manifest.
2. Creates independent train, validation, and test partitions.
3. Preprocesses each partition using MediaPipe.
4. Trains the custom gesture classifier.
5. Evaluates and exports `gesture_recognizer.task`.

Omitting `--manifest-path` enables legacy image-level random splitting for prototype experiments. Results from that mode must not be treated as independent recognition benchmarks.

## Application-to-WSL Training

The main application uses:

- `TrainingJob` — job configuration and path validation
- `run_repo_wsl_training_job()` — launches the repository's WSL training environment
- `run_training_pipeline()` — coordinates training, inference evaluation, acceptance, and activation

The Windows-to-WSL handoff has been exercised successfully using the repository-contained training environment.

The complete Python pipeline has also been tested successfully with a grouped prototype dataset.

## Model Acceptance, Activation, and Rollback

After training, the application evaluates the exported model against the held-out test partition.

`model_acceptance.py` checks:
- Minimum evaluation samples per class
- Per-class precision and recall
- Background false-positive rate
- Confusion between new and existing gestures

Acceptance thresholds are configurable and require validation using representative capture data.

`training_pipeline.py` verifies the candidate's SHA-256 fingerprint before activation.

If the candidate passes, `model_activation.py` validates the MediaPipe model, preserves the previous active model as a backup, and replaces the active model file.

If training, evaluation, or acceptance fails, the existing active model must remain unchanged.

`rollback_model()` can restore the saved previous model. Automatic rollback after a later runtime failure is not yet part of the integrated application workflow.

## Testing

From the repository root with the main Python 3.11 environment active:

```bash
python -m pytest -q tests/unit/test_training_pipeline.py
python -m pytest -q tests/unit/test_model_acceptance.py
python -m pytest -q tests/unit/test_model_activation.py
python -m pytest -q tests/integration/test_multigesture_training_contract.py
```

These regression tests do not require Model Maker training during CI.

Additional manual smoke tests have verified:
- Model Maker training in WSL
- Windows application-to-WSL execution
- Grouped dataset preparation and training
- Exported-model inference and acceptance
- Model activation and rollback
- R04 enrollment manifest compatibility
- Preservation of multiple enrolled gesture datasets

Prototype performance results are not evidence of generalizable accuracy because the sample groups were simulated rather than independently collected.

## Current Limitations / Sprint 6 Integration

- The frontend enrollment workflow and R04 training orchestration are not connected end to end.
- The proposed HTTP training-service contract requires team coordination and implementation.
- Live recognition must be connected to newly activated models.
- Real enrollment datasets and acceptance thresholds require further validation.
- Training currently launches a new Model Maker process, including its initialization overhead.
- Native training setup outside the verified Windows/WSL environment remains unverified.

The goal for Sprint 6 is to integrate these components without changing the verified training and model-safety boundaries unnecessarily.
