"""Command authorization policy for SOC 2 Control 01, Keyboard Command Authorization.

This module is the one place that says which presentation commands exist and which of
them a gesture profile may trigger. The controller validates every binding against it
before a profile is activated, and checks it again at dispatch.

It only describes commands by name. Which physical key a command presses stays with the
presentation adapter. See docs/soc2-control-01/command-authorization-contract.md.
"""

import re
from collections.abc import Mapping
from typing import Any

# Every presentation command SlideKick knows about.
APPROVED_COMMANDS: frozenset[str] = frozenset(
    {"next", "previous", "pause", "resume", "end"}
)

# Commands a gesture profile may bind. "end" is left out on purpose: finishing a
# presentation is a lifecycle or manual action, so a mapping mistake in a profile
# cannot close the slideshow. Move "end" in here only after the team agrees.
PROFILE_BINDABLE_COMMANDS: frozenset[str] = frozenset(
    {"next", "previous", "pause", "resume"}
)

# Lowercase letters, digits and underscores, starting with a letter. This checks the
# shape of a gesture id. Which ids actually exist belongs to the recognition owner.
GESTURE_ID_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}")


class InvalidGestureBindingError(ValueError):
    """A gesture to command mapping was rejected before it could be used."""


def is_profile_bindable(command: Any) -> bool:
    """True only for a string that is exactly one of the bindable command names."""
    return isinstance(command, str) and command in PROFILE_BINDABLE_COMMANDS


def _describe(value: Any) -> str:
    """Short, safe description of a rejected value for error messages."""
    if isinstance(value, str):
        shown = value if len(value) <= 40 else value[:40] + "..."
        return repr(shown)
    return f"a {type(value).__name__}"


def validate_gesture_bindings(bindings: Any) -> dict[str, str]:
    """Return a clean copy of bindings, or raise InvalidGestureBindingError.

    Every problem is reported together so a bad profile can be fixed in one pass.
    Nothing is returned for a partly valid mapping.
    """
    if not isinstance(bindings, Mapping):
        raise InvalidGestureBindingError(
            f"gesture bindings must be a mapping, got {_describe(bindings)}"
        )

    validated: dict[str, str] = {}
    problems: list[str] = []

    for gesture, command in bindings.items():
        gesture_ok = isinstance(gesture, str) and GESTURE_ID_PATTERN.fullmatch(gesture)
        if not gesture_ok:
            problems.append(
                f"gesture id {_describe(gesture)} is not a valid identifier"
            )
            continue
        if not is_profile_bindable(command):
            problems.append(
                f"gesture {gesture!r} maps to {_describe(command)}, "
                f"which is not a bindable command"
            )
            continue
        validated[gesture] = command

    if problems:
        raise InvalidGestureBindingError("; ".join(problems))

    return validated
