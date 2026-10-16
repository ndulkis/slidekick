# SlideKick

Control presentations with hand gestures. SlideKick watches a webcam, recognizes swipes, and sends slide commands (next, previous) to whatever presentation app is in focus.

| Area | Tools |
| --- | --- |
| Backend / ML | Python 3.11, MediaPipe, OpenCV, NumPy |
| Slide control | `pyautogui` keystrokes |
| Dashboard | React 19, TypeScript, Vite |
| Quality | Ruff, pytest, oxlint, Vitest, GitHub Actions |

Runs on macOS and Windows. CI runs on Linux.

## Setup

**Prerequisites:** Python 3.11, Node 20, Git.

**macOS**

```bash
git clone git@github.com:ndulkis/slidekick.git && cd slidekick
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
npm --prefix frontend ci
./scripts/verify.sh
```

**Windows (PowerShell)**

```powershell
git clone git@github.com:ndulkis/slidekick.git; cd slidekick
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.lock
npm --prefix frontend ci
$env:PYTHONPATH = "src"; python scripts/check_env.py
```

- Activate `.venv` in every new terminal.
- If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
- On Windows, run `verify.sh` from Git Bash.
- After pulling, if the environment check fails, rerun `pip install -r requirements.lock` or `npm --prefix frontend ci`.

## Commands

Run from the repo root with `.venv` active. On Windows, set `$env:PYTHONPATH = "src"` instead of the `PYTHONPATH=src` prefix.

| Command | What it does |
| --- | --- |
| `PYTHONPATH=src python scripts/run_gesture_control.py` | Run SlideKick: webcam gestures control the focused presentation |
| `PYTHONPATH=src python -m slidekick.recognition.camera` | Camera and recognition only (prints events, no slide control) |
| `PYTHONPATH=src python scripts/check_env.py` | Check the dev environment and print fixes |
| `./scripts/verify.sh` | Run the environment check plus the main CI checks |
| `./scripts/checks/<name>.sh` | Run one CI check on its own, e.g. `./scripts/checks/unit-tests.sh` (see `scripts/checks/` for the list) |
| `python -m pytest` | Run all Python tests |
| `ruff check .` / `ruff format .` | Lint / format Python |
| `npm --prefix frontend run dev` | Dashboard dev server on port 5173 |
| `npm --prefix frontend run test` / `run lint` | Frontend tests / lint |
| `python manual_test.py` | Press "next slide" once after 3 seconds, to check slide control |

**Permissions:**
- **macOS:** System Settings → Privacy & Security. Give your terminal **Camera**, **Accessibility** (key presses) and **Screen Recording** (end-to-end latency test only).
- **Windows:** Settings → Privacy & security → Camera, including **Let desktop apps access your camera**.

## Configuration

Every setting is optional. To override one, copy `.env.example` to `.env`. Real environment variables take priority over `.env`, which takes priority over the defaults in `src/slidekick/config.py`.

| Variable | Default | Allowed values |
| --- | --- | --- |
| `SLIDEKICK_ENV` | `development` | `development`, `test`, `production` |
| `SLIDEKICK_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SLIDEKICK_MODEL_PATH` | `models/gesture_recognizer.task` | Path relative to the repo root |
| `SLIDEKICK_CAMERA_INDEX` | `0` | `0`, `1`, `2`, ... |
| `SLIDEKICK_CAMERA_BACKEND` | `avfoundation` (macOS), `msmf` (Windows), `v4l2` (Linux) | That OS's default, `any`, or `dshow` on Windows |

Never commit real secrets. Add the name to `.env.example` with an empty value, and put CI secrets under GitHub **Settings → Secrets and variables → Actions**.

## Tests

| Folder | What it covers | In CI |
| --- | --- | --- |
| `tests/unit/` | Individual modules | Yes |
| `tests/integration/` | Recognition event → controller → adapter | Yes |
| `tests/recognition/` | Swipe recognizer | Yes |
| `tests/smoke/` | Slide-control path | Yes |
| `tests/environment/` | Python/Node versions stay in sync across config files | Yes |
| `tests/performance/` | Latency benchmarks and command safety (see below) | Yes, except end-to-end |

`tests/conftest.py` fakes `pyautogui`, since CI has no display.

### Latency tests

**Recognition → command** (mock adapter, runs anywhere):

```bash
python -m pytest tests/performance -s -k recognition_to_command
```

**End-to-end: recognition → key press → visible slide change** (local only, macOS or Windows):

1. Make a slide deck in PowerPoint, Keynote or Google Slides: slide 1 solid black, slide 2 solid white, no transitions.
2. Run the command below. During the 5-second countdown, start the slideshow on slide 1, fullscreen on your main monitor.
3. Don't touch the mouse or keyboard until the slides stop flipping.

```bash
SLIDEKICK_E2E=1 SLIDEKICK_PERF_NOTE="Keynote, MacBook Air M2" python -m pytest tests/performance -s -k end_to_end
```

The recognition → command test only prints its results. Every end-to-end run is saved to `perf-results/`:

| File | Contents |
| --- | --- |
| `summary.csv` | One row per run: median, p95, min, max, commit, OS, Python, and your `SLIDEKICK_PERF_NOTE` |
| `<timestamp>_<test>.csv` | Raw per-sample times for that run |

Use `SLIDEKICK_PERF_NOTE` to record test conditions (app, machine, lighting). Neither test includes webcam capture or MediaPipe inference, so they don't measure the 200 ms target on their own.

## CI

`.github/workflows/ci.yml` runs on every push and on PRs into `develop` or `production`:

| Job | Runs |
| --- | --- |
| Lint and Unit Tests | Environment check, Ruff lint + format, environment/unit/integration/recognition/performance tests (latency shown in the job summary) |
| Gesture Smoke Tests | `tests/smoke` |
| Frontend | oxlint, type check, Vitest, production build |
| Security Checks | Gitleaks, pip-audit, Bandit, `npm audit` (report only) |

## Python dependencies

Edit `requirements.in`, never `requirements.lock`. To add a package:

1. Add it to `requirements.in`.
2. Run `pip-compile --no-emit-index-url --output-file=requirements.lock --strip-extras requirements.in`.
3. Check the lock diff. Running pip-compile on a Mac adds macOS-only packages (`pyobjc-*`) and drops Windows ones (`colorama`). Remove or restore those by hand, or CI and Windows installs break.
4. Run `pip install -r requirements.lock`, then commit both files.

MediaPipe stays below 1.0 because 1.0.x crashes on Apple Silicon.

## Branching

Branch from `develop` and open PRs back into `develop`. Release by merging `develop` into `production` through a PR.

## Docs

| Doc | Topic |
| --- | --- |
| [build.md](docs/build.md) | From a clean checkout to a validated build |
| [architecture-decision-note.md](docs/architecture-decision-note.md) | Architecture decisions |
| [observer-event-contract.md](docs/observer-event-contract.md) | Recognition event format |
| [session-state-model.md](docs/session-state-model.md) | Session states |
| [S2-R04-T1-Command-Mapping-Spec.md](docs/S2-R04-T1-Command-Mapping-Spec.md) | Gesture-to-command mapping |
| [ui-states.md](docs/ui-states.md), [accessibility-personas.md](docs/accessibility-personas.md), [keyboard-nav-testing.md](docs/keyboard-nav-testing.md) | Dashboard UX and accessibility |
| [risk-log.md](docs/risk-log.md) | Project risks |
| [lando-rollout-changes.md](docs/lando-rollout-changes.md) | How CI changed when Docker/Lando were removed |
