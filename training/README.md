# SlideKick Custom Gesture Training

## Overview

SlideKick uses MediaPipe Model Maker to train custom hand gesture recognition models from labeled image datasets.

Training runs in a separate Python 3.10 environment because its dependencies differ from those of the main SlideKick application.

## Requirements

- Python 3.10
- Dependencies listed in `training/requirements.txt`
- A labeled gesture image dataset containing a `none` class and at least one custom gesture class

## Training

Run the training script using the dedicated training environment:

```bash
python training/scripts/train_prototype.py \
  --dataset-dir /path/to/dataset \
  --export-dir /path/to/new/export-directory
```

The export directory must not already exist.

## Output

Successful training produces a MediaPipe `gesture_recognizer.task` model in the specified export directory.

## Integration

The main SlideKick application uses `TrainingJob` and `training_runner.py` to launch training in an external Python environment. On Windows, the WSL runner supports execution using the separate Linux training environment.

`dataset_preparation.py` prepares enrollment images and negative samples into the labeled directory structure expected by Model Maker.

Model validation, activation, and rollback are handled separately by `model_activation.py`.

## Current Limitations

- Guided enrollment and training orchestration are not yet fully integrated.
- Dataset splitting in the trainer currently uses random image-level partitions; capture-group-aware splitting is implemented separately but not yet connected.
- Training is synchronous, and starting a new process requires importing Model Maker again.
- Native training setup on teammates' operating systems has not yet been verified.