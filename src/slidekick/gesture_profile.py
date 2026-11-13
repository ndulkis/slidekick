"""Gesture profiles for SlideKick, Sprint 4 task S4-R01-T2.

A profile is a named set of gesture to command bindings. This module turns profile data
from a JSON file or a Python mapping into an immutable GestureProfile, and refuses
anything that breaks the contract in docs/sprint4/S4-R01-T1-Interface-Contracts.md.

Loading a profile has no side effects. It never presses a key and never touches a
session. Activating a profile is the job of SessionCoordinator.apply_profile.
"""

import json
import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .command_policy import InvalidGestureBindingError, validate_gesture_bindings
from .gesture_command_controller import DEFAULT_GESTURE_BINDINGS

PROFILE_VERSION = 1
MAX_PROFILE_BYTES = 64 * 1024
PROFILE_FIELDS = frozenset({"version", "name", "bindings"})

# Letters, digits, spaces, underscores, dots and hyphens. Starts with a letter or digit.
# The name is shown in the UI and written to logs, so it stays plain text.
PROFILE_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}")


class InvalidProfileError(ValueError):
    """A gesture profile was rejected before it could be used."""


def _describe(value: Any) -> str:
    """Short, safe description of a rejected value for error messages."""
    if isinstance(value, str):
        shown = value if len(value) <= 40 else value[:40] + "..."
        return repr(shown)
    return f"a {type(value).__name__}"


def _name_problem(name: Any) -> str | None:
    if isinstance(name, str) and PROFILE_NAME_PATTERN.fullmatch(name):
        return None
    return f"name {_describe(name)} is not a valid profile name"


def _check_bindings(
    bindings: Any, known_gestures: frozenset[str] | None
) -> tuple[dict[str, str], list[str]]:
    """Validate bindings. Returns the clean copy and a list of problems."""
    try:
        clean = validate_gesture_bindings(bindings)
    except InvalidGestureBindingError as exc:
        return {}, [f"bindings rejected: {exc}"]

    if known_gestures is not None:
        unknown = [gesture for gesture in clean if gesture not in known_gestures]
        if unknown:
            shown = ", ".join(repr(gesture) for gesture in unknown[:5])
            return {}, [f"gestures the recognizer does not emit: {shown}"]

    return clean, []


def _as_known_set(known_gestures: Collection[str] | None) -> frozenset[str] | None:
    if known_gestures is None:
        return None
    if isinstance(known_gestures, str | bytes):
        raise TypeError(
            "known_gestures must be a collection of gesture ids, not a string"
        )
    return frozenset(known_gestures)


@dataclass(frozen=True)
class GestureProfile:
    """A named, validated and read only set of gesture to command bindings.

    Any instance that exists is valid. Building one with bad data raises
    InvalidProfileError, so code that receives a GestureProfile can trust it.
    """

    name: str
    bindings: Mapping[str, str]

    def __post_init__(self) -> None:
        problems = []
        name_problem = _name_problem(self.name)
        if name_problem:
            problems.append(name_problem)
        clean, binding_problems = _check_bindings(self.bindings, None)
        problems.extend(binding_problems)

        if problems:
            raise InvalidProfileError("; ".join(problems))

        object.__setattr__(self, "bindings", MappingProxyType(clean))


def default_profile() -> GestureProfile:
    """The built in profile. It matches profiles/default.json."""
    return GestureProfile(name="default", bindings=DEFAULT_GESTURE_BINDINGS)


def profile_from_mapping(
    data: Any, known_gestures: Collection[str] | None = None
) -> GestureProfile:
    """Build a GestureProfile from parsed data, or raise InvalidProfileError.

    The schema is strict. It needs exactly the fields version, name and bindings, and
    version must be 1. Every problem found is reported together.

    known_gestures is the set of gesture ids the recognizer can emit. When it is given,
    a profile cannot bind a gesture that will never fire. The recognition owner supplies
    that set. This module does not guess it.
    """
    known = _as_known_set(known_gestures)

    if not isinstance(data, Mapping):
        raise InvalidProfileError(f"profile must be a mapping, got {_describe(data)}")

    problems: list[str] = []

    extra = [key for key in data if key not in PROFILE_FIELDS]
    if extra:
        shown = ", ".join(_describe(key) for key in extra[:5])
        problems.append(f"unknown fields: {shown}")

    for field in ("version", "name", "bindings"):
        if field not in data:
            problems.append(f"missing field {field!r}")

    if "version" in data:
        version = data["version"]
        if type(version) is not int or version != PROFILE_VERSION:
            problems.append(f"version must be the number {PROFILE_VERSION}")

    if "name" in data:
        name_problem = _name_problem(data["name"])
        if name_problem:
            problems.append(name_problem)

    clean: dict[str, str] = {}
    if "bindings" in data:
        clean, binding_problems = _check_bindings(data["bindings"], known)
        problems.extend(binding_problems)

    if problems:
        raise InvalidProfileError("; ".join(problems))

    return GestureProfile(name=data["name"], bindings=clean)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise InvalidProfileError("profile file repeats a key")
    return dict(pairs)


def load_profile(
    path: str | Path, known_gestures: Collection[str] | None = None
) -> GestureProfile:
    """Read a JSON profile file, validate it and return it.

    A file is accepted whole or not at all. Files over 64 KB, files that are not UTF-8
    JSON, and files that repeat a key are refused. Error messages name the problem and
    quote at most 40 characters of a rejected value, so a typo is easy to find without
    echoing the file.
    """
    known = _as_known_set(known_gestures)
    file_path = Path(path)

    try:
        with file_path.open("rb") as handle:
            raw = handle.read(MAX_PROFILE_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise InvalidProfileError(
            f"cannot read profile file {file_path.name!r}"
        ) from exc

    if len(raw) > MAX_PROFILE_BYTES:
        raise InvalidProfileError(
            f"profile file is larger than {MAX_PROFILE_BYTES} bytes"
        )

    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except InvalidProfileError:
        raise
    except UnicodeDecodeError as exc:
        raise InvalidProfileError("profile file is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise InvalidProfileError(
            f"profile file is not valid JSON at line {exc.lineno}"
        ) from exc
    except RecursionError as exc:
        raise InvalidProfileError("profile file is nested too deeply") from exc

    return profile_from_mapping(data, known)
