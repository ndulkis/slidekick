# CI Workflow

## How it works

`.github/workflows/ci.yml` triggers on three events: a pull request into `develop` or `production`, a push to any branch, and a manual run from the Actions tab. Runs are deduplicated per branch, a new push cancels whatever was already running for that same branch or PR.

It runs three jobs, all on a plain Ubuntu runner:

**quality**
Installs Python 3.11 and the packages pinned in `requirements.lock`, sets `PYTHONPATH` so `import slidekick` resolves to `src/slidekick`, then runs:
- `scripts/check_env.py --ci`, confirms the Python version, installed packages, and project layout are consistent
- `ruff check`, lint
- `ruff format --check`, formatting
- `pytest tests/environment`, checks the pinned versions in this file, `requirements.lock`, and `docker/dev/Dockerfile` haven't drifted apart
- `pytest tests/unit`

**gesture-smoke-test**
Same Python setup, then runs `pytest tests/smoke`. Kept intentionally narrow: confirms a gesture result has the right shape and maps to the right command, not model accuracy. Runners have no webcam or display, so this relies on prerecorded samples and a mocked `pyautogui`.

**frontend**
Installs Node 20, runs `npm ci` against `frontend/package-lock.json`, then `npm run lint`, `npm run test`, and `npm run build`. The build step runs `tsc -b` first, so it doubles as the type check.

All three run in parallel and all three must pass. There's also a commented-out `integration` job at the bottom, inactive since `tests/integration` doesn't exist yet. It's left in as a draft for whoever picks up integration testing, not something currently running.

## What changed

This file started from a version a teammate had written, which included a fourth job, `container-build`, that built the Docker image used for local development, and a commented-out `model-evaluation` job.

- **`container-build` removed.** That job built and verified the same Docker image the local dev environment used. Since the project no longer runs on that container setup, there was nothing left for the job to build or verify against.
- **`model-evaluation` removed.** It called `scripts/evaluate_model.py` against a dataset at `tests/data/ci_validation`. Neither the script nor the dataset exist in the repo. It was commented out already, so it never ran, but leaving in a reference to files that don't exist risked someone assuming that check was real or already working.
- **`integration` kept, commented out.** Same situation, `tests/integration` doesn't exist yet, but this one reflects real planned work, integration tests are called out as a future requirement, so it's left as a labeled placeholder rather than deleted.
- **References to the old local dev tooling removed from comments.** Comments now describe what each step does on its own, without assuming a container-based dev setup as context.
- **Job names unchanged.** `quality`, `gesture-smoke-test`, and `frontend` keep their original names so any branch protection rule already requiring them by name continues to work without reconfiguration.