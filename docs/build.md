# Build

How to go from a clean checkout to a validated build, without Lando or Docker.

## Versions

- Python 3.11
- Node 20

These are pinned in `docker/dev/Dockerfile` (still the source of truth for local dev) and mirrored in `.github/workflows/ci.yml` as `PYTHON_VERSION` and `NODE_VERSION`. `tests/environment/test_environment.py` checks the two stay in sync, so if one changes, update the other in the same PR.

## Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
```

`requirements.lock` is generated from `requirements.in` with `pip-compile`. Edit `requirements.in`, never the lock file directly.

Validate:

```bash
ruff check .
ruff format --check .
python scripts/check_env.py --ci
python -m pytest -q tests/environment
python -m pytest -q tests/unit
python -m pytest -q tests/smoke
```

`check_env.py --ci` skips the checks that only apply inside a container (being in Lando, ffmpeg, Node/frontend state); everything else runs the same locally and in CI.

## Frontend

```bash
cd frontend
npm ci
```

`npm ci` installs exactly what's pinned in `package-lock.json`, unlike `npm install`, which can update it.

Validate and build:

```bash
npm run lint
npm run test
npm run build
```

`npm run build` runs `tsc -b && vite build`, producing the production bundle in `frontend/dist/`.

## CI

`.github/workflows/ci.yml` runs all of the above as three jobs on every PR into `develop` or `production`: `quality` (Python lint, format, environment/unit tests), `gesture-smoke-test` (`tests/smoke`), and `frontend` (lint, test, build). No Docker image is built. A failing job blocks merge per `docs/git-workflow.md`.

The `frontend` job uploads `frontend/dist/` as a build artifact named `frontend-dist` after a successful build, viewable from the run's Summary page and kept for 14 days. There's no equivalent backend artifact yet, since the Python side runs from source rather than a packaged build.

## Not yet in scope

- No integration test job yet; add it once cross-layer integration tests exist.
- Deployment consumes this build in a later stage (S2-CI7) and isn't part of this doc.