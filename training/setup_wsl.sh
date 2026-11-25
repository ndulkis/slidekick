
#!/usr/bin/env bash
set -euo pipefail

# Determine paths relative to this script, not the user's computer.
TRAINING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$TRAINING_DIR/.venv"

# Include the standard per-user installation directory for uv.
export PATH="$HOME/.local/bin:$PATH"

echo "SlideKick custom gesture training setup"
echo "Training directory: $TRAINING_DIR"

# Use uv to manage the dedicated Python 3.10 environment.
if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv is required for training setup."
    echo "Install uv in WSL and rerun this script."
    exit 1
fi

echo "Ensuring Python 3.10 is available..."
uv python install 3.10

echo "Creating or verifying Python 3.10 environment..."

if [ ! -f "$VENV_DIR/pyvenv.cfg" ]; then
    uv venv --no-project --python 3.10 "$VENV_DIR"
fi

PYTHON="$VENV_DIR/bin/python"

# Refuse to reuse a virtual environment with the wrong Python version.
"$PYTHON" -c \
    'import sys; assert sys.version_info[:2] == (3, 10), "Expected Python 3.10"'

echo "Installing training dependencies..."

uv pip install \
    --python "$PYTHON" \
    -r "$TRAINING_DIR/requirements.txt"

echo "Checking TensorFlow Metadata compatibility..."

"$PYTHON" -c \
    'from tensorflow_metadata.proto.v0 import anomalies_pb2; print("TensorFlow Metadata import successful")'

echo "Checking MediaPipe Model Maker installation..."

"$PYTHON" -c \
    'from mediapipe_model_maker import gesture_recognizer; print("Model Maker import successful")'

echo ""
echo "SlideKick training environment ready."
echo "Interpreter: $PYTHON"
