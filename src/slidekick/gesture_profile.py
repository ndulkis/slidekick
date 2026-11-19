"""The saved gesture profile: which gesture runs which presentation command.

The Settings page edits it through the API (api_server.py). Bindings go
through command_policy both when they are saved and when they are loaded, so a
hand-edited or corrupt file can never make an unapproved command active.
"""

import json
import logging
from collections.abc import Mapping
from pathlib import Path

from .command_policy import InvalidGestureBindingError, validate_gesture_bindings
from .gesture_command_controller import DEFAULT_GESTURE_BINDINGS

logger = logging.getLogger(__name__)

PROFILE_VERSION = 1
PROFILE_ID = "default"


def default_bindings() -> dict[str, str]:
    return dict(DEFAULT_GESTURE_BINDINGS)


def load_bindings(path: Path | None) -> dict[str, str]:
    """Read the saved bindings, falling back to the defaults if missing or bad."""
    if path is None or not path.exists():
        return default_bindings()
    try:
        return validate_gesture_bindings(json.loads(path.read_text())["bindings"])
    except (
        OSError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        InvalidGestureBindingError,
    ):
        logger.warning(
            "Ignoring unreadable gesture bindings file %s", path, exc_info=True
        )
        return default_bindings()


def save_bindings(path: Path, bindings: Mapping[str, str]) -> dict[str, str]:
    """Validate and save the bindings. Raises InvalidGestureBindingError, and
    writes nothing, if any binding is rejected by the policy.
    """
    validated = validate_gesture_bindings(bindings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "version": PROFILE_VERSION,
                "profile_id": PROFILE_ID,
                "bindings": validated,
            },
            indent=2,
        )
    )
    return validated
