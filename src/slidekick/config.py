"""Runtime settings for SlideKick.

Each setting is read from, in order of precedence:

1. a real environment variable (how CI and GitHub Actions secrets supply them)
2. a `.env` file at the repo root (local overrides; ignored by git)
3. the defaults below

Settings that depend on the operating system, like the camera backend, get
their default from the OS SlideKick is running on, so the same `.env` (or no
`.env` at all) works on macOS and Windows. See `.env.example` for the full list.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"

APP_ENVS = ("development", "test", "production")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")

# The OpenCV capture backends each OS supports. The first one is the default.
# "any" lets OpenCV pick, and works everywhere.
CAMERA_BACKENDS = {
    "macos": ("avfoundation", "any"),
    "windows": ("msmf", "dshow", "any"),
    "linux": ("v4l2", "any"),
}


class ConfigError(ValueError):
    """Raised when one or more settings are invalid. Lists every problem."""


@dataclass(frozen=True)
class Settings:
    platform: str
    app_env: str
    log_level: str
    model_path: Path
    camera_index: int
    camera_backend: str


def detect_platform(platform: str = sys.platform) -> str:
    """Return "macos", "windows", or "linux" for a `sys.platform` value."""
    if platform == "darwin":
        return "macos"
    if platform.startswith("win"):
        return "windows"
    return "linux"


def read_env_file(path: Path) -> dict[str, str]:
    """Parse simple `KEY=value` lines. Blank lines and `#` comments are skipped."""
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def load_settings(
    environ: Mapping[str, str] | None = None,
    env_file: Path = ENV_FILE,
    platform: str = sys.platform,
) -> Settings:
    """Build the settings for this machine, raising ConfigError if any are invalid."""
    values = {**read_env_file(env_file), **(os.environ if environ is None else environ)}
    os_name = detect_platform(platform)
    backends = CAMERA_BACKENDS[os_name]
    problems = []

    def choice(key: str, allowed: tuple[str, ...], default: str) -> str:
        value = values.get(key, default)
        if value not in allowed:
            problems.append(f"{key}={value!r} must be one of: {', '.join(allowed)}")
        return value

    app_env = choice("SLIDEKICK_ENV", APP_ENVS, "development")
    log_level = choice("SLIDEKICK_LOG_LEVEL", LOG_LEVELS, "INFO")
    camera_backend = choice("SLIDEKICK_CAMERA_BACKEND", backends, backends[0])

    raw_index = values.get("SLIDEKICK_CAMERA_INDEX", "0")
    camera_index = int(raw_index) if raw_index.isdigit() else -1
    if camera_index < 0:
        problems.append(
            f"SLIDEKICK_CAMERA_INDEX={raw_index!r} must be a whole number, like 0"
        )

    # Relative paths are resolved from the repo root, so they work from any
    # directory and with either slash direction on Windows.
    model_path = ROOT / values.get(
        "SLIDEKICK_MODEL_PATH", "models/gesture_recognizer.task"
    )

    if problems:
        raise ConfigError("\n".join(problems))
    return Settings(
        platform=os_name,
        app_env=app_env,
        log_level=log_level,
        model_path=model_path,
        camera_index=camera_index,
        camera_backend=camera_backend,
    )
