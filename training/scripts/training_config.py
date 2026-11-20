"""Configuration for custom gesture model training."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingConfig:
    """Internal hyperparameters for MediaPipe Model Maker."""

    learning_rate: float = 0.001
    batch_size: int = 2
    epochs: int = 10

    def validate(self) -> None:
        if not 0 < self.learning_rate <= 1:
            raise ValueError("Learning rate must be between 0 and 1")

        if self.batch_size < 1:
            raise ValueError("Batch size must be at least 1")

        if self.epochs < 1:
            raise ValueError("Epochs must be at least 1")
