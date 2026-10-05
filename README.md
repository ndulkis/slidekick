# SlideKick

Control presentations with hand gestures. SlideKick watches a webcam, recognizes gestures, and turns them into slide controls (next, previous, end) for whatever presentation app is in focus.

> **Status: early development.** The dev environment, CI, configuration, a keyboard-based presentation adapter, the dashboard shell, and a camera/gesture-recognition prototype are in place. The camera pipeline isn't connected to the slide controls yet.

## Tech stack

| Area | Tools |
| --- | --- |
| Backend / ML | Python 3.11, MediaPipe, OpenCV, NumPy |
| Slide control | `pyautogui` keystrokes |
| Dashboard | React 19, TypeScript, Vite, React Router |
| Quality | Ruff, pytest, oxlint, Vitest + Testing Library |
| Environment | Python virtual environment (`.venv`), Node 20, GitHub Actions |

Runs on macOS and Windows. CI runs on Linux.

## Repository layout

```
.
├── src/slidekick/        Python package: config, presentation adapters, recognition/ (camera + gestures)
├── tests/                Python tests: unit/, smoke/, environment/
├── frontend/             Dashboard app: Dashboard, Session, and Settings pages
├── docs/                 Design, build, and testing notes
├── data/, models/        Local datasets and the gesture model (gesture_recognizer.task)
├── scripts/              Dev scripts: check_env.py (environment doctor), verify.sh (run everything CI runs)
├── .env.example          Every configuration setting, documented
├── .python-version       Python version the project targets
├── .nvmrc                Node version the project targets
├── manual_test.py        Check that the keyboard adapter changes slides on your machine
├── requirements.in       Direct Python dependencies (edit this)
└── requirements.lock     Pinned versions generated from requirements.in (don't edit)
```

## Getting started

**Prerequisites:** Python 3.11, Node 20, and Git. Docker and Lando are no longer used.

| | macOS | Windows |
| --- | --- | --- |
| Python 3.11 | `brew install python@3.11` or [pyenv](https://github.com/pyenv/pyenv) | [python.org installer](https://www.python.org/downloads/) (includes the `py` launcher) |
| Node 20 | `nvm install` (reads `.nvmrc`) or `brew install node@20` | [nodejs.org installer](https://nodejs.org/) or [nvm-windows](https://github.com/coreybutler/nvm-windows) |
| Git | Xcode Command Line Tools | [Git for Windows](https://git-scm.com/download/win) (includes Git Bash) |

**macOS**

```bash
git clone git@github.com:ndulkis/slidekick.git
cd slidekick

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
npm --prefix frontend ci

./scripts/verify.sh
```

**Windows (PowerShell)**

```powershell
git clone git@github.com:ndulkis/slidekick.git
cd slidekick

py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.lock
npm --prefix frontend ci

$env:PYTHONPATH = "src"
python scripts/check_env.py
```

If PowerShell won't run `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt with `.venv\Scripts\activate.bat`. `verify.sh` is a bash script, so on Windows run it from **Git Bash** after `source .venv/Scripts/activate`.

Your prompt shows `(.venv)` while the environment is active. Activate it again in every new terminal. `pytest.ini` and `verify.sh` put `src/` on `PYTHONPATH`, so `import slidekick` works without an install step.

### Verify your setup

| Command | When to use it |
| --- | --- |
| `python scripts/check_env.py` | Fast environment check (a few seconds). Prints a fix for anything wrong. Needs `PYTHONPATH=src`. |
| `./scripts/verify.sh` | Runs the check above, then every check CI runs. If this passes, CI should too. |

`check_env.py` checks that:

- the Python version matches `.python-version` and the Node version matches `.nvmrc`
- `import slidekick` resolves to `src/slidekick`
- installed Python packages match `requirements.lock`
- `frontend/node_modules` matches `package-lock.json`
- NumPy, OpenCV, Ruff, pytest, and pip-compile all work
- `.env.example` exists, your configuration is valid for your OS, and the gesture model exists
- `data/` and `models/` are writable

The most common fixes are `pip install -r requirements.lock` (after someone changes the lock file) and `npm --prefix frontend ci` (frontend dependencies are missing or stale). Run the check again after pulling changes that touch either.

A successful `verify.sh` ends with `All checks passed. Your environment matches CI.`

## Configuration

Settings are read in this order, highest priority first:

1. Real environment variables (how CI supplies them)
2. A `.env` file at the repo root (local overrides; git ignores it)
3. Defaults in `src/slidekick/config.py`

Every setting is optional, so most people don't need a `.env`. To override one, copy `.env.example` to `.env` (`cp` on macOS, `copy` on Windows) and uncomment what you need.

| Variable | Default | Allowed values |
| --- | --- | --- |
| `SLIDEKICK_ENV` | `development` | `development`, `test`, `production` |
| `SLIDEKICK_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SLIDEKICK_MODEL_PATH` | `models/gesture_recognizer.task` | Any path, relative to the repo root |
| `SLIDEKICK_CAMERA_INDEX` | `0` | `0` for the default webcam, `1`, `2`, ... for others |
| `SLIDEKICK_CAMERA_BACKEND` | Depends on your OS | See below |

SlideKick detects your OS at startup and defaults to its camera backend:

| OS | Default backend | Also allowed |
| --- | --- | --- |
| macOS | `avfoundation` | `any` |
| Windows | `msmf` | `dshow` (try it if the camera is slow to open or shows a black frame), `any` |
| Linux (CI) | `v4l2` | `any` |

`check_env.py` reports invalid values, such as a backend from another OS. The camera prototype doesn't read these settings yet.

**Secrets:** none are needed yet. When one is, add its name to `.env.example` with an empty value (never a real one), put the real value in your `.env`, and for CI add it under GitHub **Settings → Secrets and variables → Actions** and pass it to the job with `${{ secrets.NAME }}`.

## Common commands

| Command | What it does |
| --- | --- |
Run these from the repo root with `.venv` active. The last column is the Lando command each one replaces.

| Command | What it does | Was |
| --- | --- | --- |
| `python scripts/check_env.py` | Check the dev environment and suggest fixes | `lando doctor` |
| `./scripts/verify.sh` | Run the environment check plus all CI checks, with a summary | `lando verify` |
| `python` | Python REPL | `lando python` |
| `python -m pytest` | Run the Python tests | `lando test` |
| `ruff check .` | Lint Python with Ruff | `lando lint` |
| `ruff format .` | Format Python with Ruff | `lando format` |
| `PYTHONPATH=src python -m slidekick.recognition.camera` | Run the camera and gesture-recognition prototype (macOS; see [Running the camera prototype](#running-the-camera-prototype) for Windows) | |
| `npm --prefix frontend run dev` | Start the Vite dev server on port 5173 | `lando frontend-dev` |
| `npm --prefix frontend run test` | Run the frontend tests | `lando frontend-test` |
| `npm --prefix frontend run lint` | Lint the frontend with oxlint | `lando frontend-lint` |
| `npm --prefix frontend <args>` | Run any npm command inside `frontend/` | `lando npm <args>` |
| `pip-compile --no-index --output-file=requirements.lock --strip-extras requirements.in` | Regenerate `requirements.lock` | `lando lock` |
| `pip install -r requirements.lock` | Reinstall dependencies (e.g. after the lock changes) | `lando rebuild -y` |

## Python dependencies

`requirements.in` lists the direct dependencies. `requirements.lock` pins every version and is what your `.venv` and CI install.

To add or change a dependency:

1. Edit `requirements.in`.
2. Run `pip-compile --no-index --output-file=requirements.lock --strip-extras requirements.in`.
3. Run `pip install -r requirements.lock`.
4. Commit both files.

MediaPipe is pinned below 1.0 (`mediapipe<1`) because 1.0.x crashes on startup on Apple Silicon Macs. 0.10.x works on macOS and Windows.

## Running the camera prototype

**macOS**

```bash
PYTHONPATH=src python -m slidekick.recognition.camera
```

**Windows (PowerShell)**

```powershell
$env:PYTHONPATH = "src"
python -m slidekick.recognition.camera
```

Run it from the repo root with `.venv` active. It has to run as a module (`-m`), not by file path, because `camera.py` imports the other files in `recognition/` as part of the package. A window shows the camera feed with the detected hand skeleton. Press `q` or close the window to stop.

- **macOS:** allow camera access for your terminal in System Settings → Privacy & Security → Camera.
- **Windows:** allow camera access in Settings → Privacy & security → Camera, including **Let desktop apps access your camera**.

## Testing slide control on your machine

```bash
pip install pyautogui
python manual_test.py
```

You have 3 seconds to click into an open presentation. It should move forward one slide. On macOS, give your terminal Accessibility permission first (System Settings → Privacy & Security → Accessibility). Windows needs no extra permission.

## CI

`.github/workflows/ci.yml` runs on pushes to every branch and on pull requests into `develop` or `production`. It installs Python and Node directly on an Ubuntu runner (no Docker) and runs four jobs in parallel:

| Job | What it runs |
| --- | --- |
| Lint and Unit Tests | `check_env.py --ci`, `ruff check`, `ruff format --check`, `tests/environment`, `tests/unit` |
| Gesture Smoke Tests | `tests/smoke` |
| Frontend | oxlint, an explicit TypeScript type check, Vitest, a production build, and uploads the build as the `frontend-dist` artifact |
| Security Checks | Gitleaks (committed secrets), pip-audit (Python dependency vulnerabilities), Bandit (Python source in `src/`), and `npm audit` (report only, doesn't fail the job) |

Integration tests are stubbed out at the bottom of the workflow. When enabled, they run only on pushes to `production`.

Run `./scripts/verify.sh` before pushing to catch the same failures locally.

### Python test suites

| Folder | Purpose |
| --- | --- |
| `tests/unit/` | Fast tests for individual modules, including configuration |
| `tests/smoke/` | End-to-end checks of the slide-control path. Later: model loads, a sample input is processed, commands map correctly. No retraining. |
| `tests/environment/` | Fails if the versions in `.python-version`, `.nvmrc`, `ci.yml`, and `requirements.lock` drift apart |

`tests/conftest.py` provides a fake `pyautogui`, since CI has no display. `python -m pytest` runs all three suites.

## Branching

- `production`: stable, default branch
- `develop`: integration branch
- Feature branches: branch from `develop`, then open a PR back into `develop`

When `develop` is ready to release, merge it into `production` with a PR.

## Docs

- [Build](docs/build.md): from a clean checkout to a validated build
- [Lando rollout changes](docs/lando-rollout-changes.md): how CI changed when Lando and Docker were removed
- [UI states](docs/ui-states.md): dashboard states to support, plus accessibility personas
- [Keyboard navigation testing](docs/keyboard-nav-testing.md): manual accessibility test results for the dashboard shell
