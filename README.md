# SlideKick

Control presentations with hand gestures. SlideKick watches a webcam, recognizes gestures, and turns them into slide controls (next, previous, end) for whatever presentation app is in focus.

> **Status: early development.** The dev environment, CI, a keyboard-based presentation adapter, and the dashboard shell are in place. Gesture recognition and the camera pipeline are not built yet.

## Tech stack

| Area | Tools |
| --- | --- |
| Backend / ML | Python 3.11, OpenCV (headless), NumPy |
| Slide control | `pyautogui` keystrokes (runs on the host) |
| Dashboard | React 19, TypeScript, Vite, React Router |
| Quality | Ruff, pytest, oxlint, Vitest + Testing Library |
| Environment | Docker via [Lando](https://lando.dev), GitHub Actions |

## Repository layout

```
.
├── src/slidekick/        Python package (presentation adapters, future gesture code)
├── tests/                Python tests: unit/, smoke/, environment/
├── frontend/             Dashboard app: Dashboard, Session, and Settings pages
├── docs/                 Design and testing notes
├── docker/dev/           Dockerfile for the Lando dev container
├── data/, models/        Local datasets and model files (git-ignored, not in the image)
├── scripts/              Dev scripts: check_env.py (`lando doctor`), verify.sh (`lando verify`)
├── manual_test.py        Host-only check that the keyboard adapter changes slides
├── requirements.in       Direct Python dependencies (edit this)
└── requirements.lock     Pinned versions generated from requirements.in (don't edit)
```

## Getting started

**Prerequisites:** [Docker](https://www.docker.com/) and [Lando](https://docs.lando.dev/install/). You don't need Python or Node installed on your machine.

```bash
git clone git@github.com:ndulkis/slidekick.git
cd slidekick

lando start          # build and start the dev container
lando npm ci         # install frontend dependencies
lando verify         # confirm your environment is set up correctly
lando frontend-dev   # dashboard at http://localhost:5173
```

The repo is mounted into the container at `/app`, and `src/` is on `PYTHONPATH`, so `import slidekick` works without an install step.

### Verify your setup

| Command | When to use it |
| --- | --- |
| `lando doctor` | Fast environment check (a few seconds). Prints a fix for anything wrong. |
| `lando verify` | Runs `doctor`, then every check CI runs. If this passes, CI should too. |

`doctor` checks that:

- you're inside the container, with the repo at `/app`
- the Python and Node versions match `docker/dev/Dockerfile`
- installed Python packages match `requirements.lock`
- `frontend/node_modules` matches `package-lock.json`
- NumPy, OpenCV, ffmpeg, Ruff, pytest, and pip-compile all work
- `data/` and `models/` are writable

The most common fixes are `lando rebuild -y` (the image is out of date, e.g. after someone changes the Dockerfile or lock file) and `lando npm ci` (frontend dependencies are missing or stale). Run `lando doctor` again after pulling changes that touch either.

## Common commands

| Command | What it does |
| --- | --- |
| `lando doctor` | Check the dev environment and suggest fixes |
| `lando verify` | Run `doctor` plus all CI checks, with a summary |
| `lando shell` | Open a bash shell in the container |
| `lando python` | Python REPL |
| `lando test` | Run the Python tests |
| `lando lint` | Lint Python with Ruff |
| `lando format` | Format Python with Ruff |
| `lando frontend-dev` | Start the Vite dev server on port 5173 |
| `lando frontend-test` | Run the frontend tests |
| `lando frontend-lint` | Lint the frontend with oxlint |
| `lando npm <args>` | Run any npm command inside `frontend/` |
| `lando lock` | Regenerate `requirements.lock` |
| `lando rebuild -y` | Rebuild the container (e.g. after changing dependencies) |

## Python dependencies

`requirements.in` lists the direct dependencies. `requirements.lock` pins every version and is what the Docker image and CI install.

To add or change a dependency:

1. Edit `requirements.in`.
2. Run `lando lock`.
3. Run `lando rebuild -y`.
4. Commit both files.

## Testing slide control on your machine

The container has no display, so anything that presses keys has to run on the host:

```bash
pip install pyautogui
python manual_test.py
```

You have 3 seconds to click into an open presentation. It should move forward one slide. On macOS, give your terminal Accessibility permission first.

## CI

`.github/workflows/ci.yml` runs on pushes to every branch and on pull requests into `develop` or `production`. It runs four jobs in parallel:

| Job | What it runs |
| --- | --- |
| Lint and Unit Tests | `check_env.py --ci`, `ruff check`, `ruff format --check`, `tests/environment`, `tests/unit` |
| Gesture Smoke Tests | `tests/smoke` |
| Frontend | oxlint, Vitest, and a production build (which also type-checks) |
| Verify Docker Build | builds `docker/dev/Dockerfile` |

Model evaluation and integration tests are stubbed out at the bottom of the workflow. When enabled, they run only on pushes to `production`.

Run `lando verify` before pushing to catch the same failures locally.

### Python test suites

| Folder | Purpose |
| --- | --- |
| `tests/unit/` | Fast tests for individual modules |
| `tests/smoke/` | End-to-end checks of the slide-control path. Later: model loads, a sample input is processed, commands map correctly. No retraining. |
| `tests/environment/` | Fails if the Python or Node versions in the Dockerfile, `ci.yml`, and `requirements.lock` drift apart |

`tests/conftest.py` provides a fake `pyautogui`, since neither Lando nor CI has a display. `lando test` runs all three suites.

## Branching

- `production`: stable, default branch
- `develop`: integration branch
- Feature branches: branch from `develop`, then open a PR back into `develop`

When `develop` is ready to release, merge it into `production` with a PR.

## Docs

- [Environment verification](docs/environment-verification.md): where teammates record proof their setup works
- [UI states](docs/ui-states.md): dashboard states to support, plus accessibility personas
- [Keyboard navigation testing](docs/keyboard-nav-testing.md): manual accessibility test results for the dashboard shell
