#!/usr/bin/env python3
"""Check that the SlideKick dev environment is set up correctly.

Run it with `PYTHONPATH=src python scripts/check_env.py` (or via
scripts/verify.sh). It uses only the standard library, so it still gives a
useful report when dependencies are missing or out of date.

CI runs it with `--ci`, which skips the frontend checks: the Python CI job
doesn't install Node dependencies, and the frontend job covers them.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

PASS, WARN, FAIL = "pass", "warn", "fail"


@dataclass
class Result:
    status: str
    name: str
    detail: str = ""
    fix: str = ""


# --- helpers -----------------------------------------------------------------


def pinned_versions() -> tuple[str, str]:
    """Return the (python, node major) versions from .python-version and .nvmrc."""
    python = (ROOT / ".python-version").read_text().strip()
    node = (ROOT / ".nvmrc").read_text().strip().lstrip("v")
    return python, node


def locked_packages() -> dict[str, str]:
    pins = {}
    for line in (ROOT / "requirements.lock").read_text().splitlines():
        match = re.match(r"^([A-Za-z0-9._-]+)==([^\s;]+)", line)
        if match:
            pins[match.group(1)] = match.group(2)
    return pins


def run(cmd: list[str], cwd: Path = ROOT, timeout: int = 60):
    # Callers inspect returncode themselves, so a failing command isn't an error.
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )


# --- checks ------------------------------------------------------------------


def check_python_version() -> Result:
    expected, _ = pinned_versions()
    actual = f"{sys.version_info.major}.{sys.version_info.minor}"
    name = "Python version matches .python-version"
    if actual != expected:
        return Result(
            FAIL,
            name,
            f"running {actual}, .python-version pins {expected}",
            f"Install Python {expected} (e.g. `pyenv install {expected}`) and "
            "recreate your virtualenv with it.",
        )
    return Result(PASS, name, actual)


def check_slidekick_importable() -> Result:
    name = "`import slidekick` resolves to src/slidekick"
    spec = importlib.util.find_spec("slidekick")
    expected = ROOT / "src" / "slidekick"
    locations = (
        [Path(p) for p in (spec.submodule_search_locations or [])] if spec else []
    )
    if expected not in locations:
        return Result(
            FAIL,
            name,
            f"PYTHONPATH={os.environ.get('PYTHONPATH', '(unset)')}",
            "Run with `PYTHONPATH=src` from the repo root.",
        )
    return Result(PASS, name)


def check_python_packages() -> Result:
    name = "Installed Python packages match requirements.lock"
    missing, mismatched = [], []
    for package, pinned in locked_packages().items():
        try:
            installed = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            missing.append(package)
            continue
        if installed != pinned:
            mismatched.append(f"{package} {installed} (lock: {pinned})")

    if missing or mismatched:
        lines = []
        if missing:
            lines.append("missing: " + ", ".join(missing))
        if mismatched:
            lines.append("wrong version: " + ", ".join(mismatched))
        return Result(
            FAIL,
            name,
            "\n".join(lines),
            "Run `pip install -r requirements.lock` in your virtualenv.",
        )
    return Result(PASS, name, f"{len(locked_packages())} packages")


def check_opencv() -> Result:
    name = "NumPy and OpenCV work"
    try:
        import cv2
        import numpy as np

        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        ok, encoded = cv2.imencode(".png", frame)
        decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if not ok or decoded.shape != frame.shape:
            raise RuntimeError("PNG encode/decode round trip failed")
    except Exception as exc:  # noqa: BLE001 - report any failure to the user
        return Result(
            FAIL,
            name,
            str(exc),
            "Run `pip install -r requirements.lock` in your virtualenv.",
        )
    return Result(PASS, name, f"numpy {np.__version__}, opencv {cv2.__version__}")


def check_commands(commands: list[str], name: str, fix: str) -> Result:
    missing = [cmd for cmd in commands if shutil.which(cmd) is None]
    if missing:
        return Result(FAIL, name, "not found: " + ", ".join(missing), fix)
    return Result(PASS, name, ", ".join(commands))


def check_node_version() -> Result:
    name = "Node version matches .nvmrc"
    _, expected = pinned_versions()
    fix = f"Install Node {expected} (e.g. `nvm install` from the repo root)."
    if shutil.which("node") is None:
        return Result(FAIL, name, "node not found", fix)
    actual = run(["node", "--version"]).stdout.strip()  # e.g. v20.19.2
    if actual.lstrip("v").split(".")[0] != expected:
        return Result(
            FAIL,
            name,
            f"running {actual}, .nvmrc pins {expected}.x",
            fix,
        )
    return Result(PASS, name, actual)


def check_node_modules() -> Result:
    name = "Frontend dependencies installed and match package-lock.json"
    if not (FRONTEND / "node_modules").is_dir():
        return Result(
            FAIL,
            name,
            "frontend/node_modules is missing",
            "Run `npm --prefix frontend ci`.",
        )
    if shutil.which("npm") is None:
        return Result(FAIL, name, "npm not found", "Install Node (e.g. `nvm install`).")
    result = run(["npm", "ls", "--depth=0"], cwd=FRONTEND)
    if result.returncode != 0:
        problems = [
            line.strip()
            for line in (result.stdout + result.stderr).splitlines()
            if "ERR" in line or "missing" in line or "invalid" in line
        ]
        return Result(
            FAIL,
            name,
            "\n".join(problems[:5]) or "npm ls reported problems",
            "Run `npm --prefix frontend ci`.",
        )
    return Result(PASS, name)


def check_writable_dirs() -> Result:
    name = "data/ and models/ exist and are writable"
    problems = []
    for folder in ("data", "models"):
        path = ROOT / folder
        if not path.is_dir():
            problems.append(f"{folder}/ is missing")
        elif not os.access(path, os.W_OK):
            problems.append(f"{folder}/ is not writable")
    if problems:
        return Result(
            FAIL,
            name,
            ", ".join(problems),
            "Restore the folders with `git checkout -- data models`.",
        )
    return Result(PASS, name)


def check_git() -> Result:
    name = "git can read the repo"
    if shutil.which("git") is None:
        return Result(WARN, name, "git not found", "Install git.")
    result = run(["git", "rev-parse", "--is-inside-work-tree"])
    if result.returncode != 0:
        return Result(
            WARN,
            name,
            result.stderr.strip().splitlines()[0] if result.stderr else "",
            "Run `git config --global --add safe.directory <repo path>`.",
        )
    return Result(PASS, name)


def check_python_tools() -> Result:
    return check_commands(
        ["ruff", "pytest", "pip-compile"],
        "Python dev tools on PATH",
        "Run `pip install -r requirements.lock` in your virtualenv.",
    )


SECTIONS = {
    "Python": [
        check_python_version,
        check_slidekick_importable,
        check_python_packages,
        check_opencv,
        check_python_tools,
    ],
    "Frontend": [check_node_version, check_node_modules],
    "Project": [check_writable_dirs, check_git],
}

# Skipped with --ci: the Python CI job doesn't install frontend deps (the
# frontend job covers those).
FRONTEND_CHECKS = {check_node_version, check_node_modules}


# --- output ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--ci",
        action="store_true",
        help="skip the frontend checks, as the Python CI job does",
    )
    args = parser.parse_args(argv)

    color = sys.stdout.isatty() and "NO_COLOR" not in os.environ

    def paint(text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if color else text

    symbols = {
        PASS: paint("✓", "32"),
        WARN: paint("!", "33"),
        FAIL: paint("✗", "31"),
    }
    counts = {PASS: 0, WARN: 0, FAIL: 0}

    print(paint("SlideKick environment check" + (" (CI mode)" if args.ci else ""), "1"))
    for section, checks in SECTIONS.items():
        if args.ci:
            checks = [check for check in checks if check not in FRONTEND_CHECKS]
            if not checks:
                continue
        print(f"\n{paint(section, '1')}")
        for check in checks:
            try:
                result = check()
            except Exception as exc:  # noqa: BLE001 - a broken check shouldn't hide the rest
                result = Result(
                    FAIL, getattr(check, "__name__", "check"), f"crashed: {exc}"
                )
            counts[result.status] += 1

            summary = f"  {symbols[result.status]} {result.name}"
            if result.status == PASS and result.detail:
                summary += paint(f"  ({result.detail})", "2")
            print(summary)
            if result.status != PASS:
                for line in result.detail.splitlines():
                    print(f"      {line}")
                if result.fix:
                    print(f"      {paint('Fix:', '1')} {result.fix}")

    print(f"\n{counts[PASS]} passed, {counts[WARN]} warnings, {counts[FAIL]} failed")
    if counts[FAIL]:
        rerun = "" if args.ci else " and run this check again"
        print(paint(f"Environment is not ready. Apply the fixes above{rerun}.", "31"))
        return 1
    print(paint("Environment looks good.", "32"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
