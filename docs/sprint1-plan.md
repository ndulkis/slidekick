# Sprint 1 Team Plan

**Owner:** Project team
**Sprint:** Sep 3–17

| Task | Plan | Evidence | Due |
|---|---|---|---|
| S1-R01-T1 | Confirm architecture boundaries, Observer contracts, branch/PR workflow, evidence model, and MVP scope | Architecture decision note, Observer event contract, sprint plan | Sep 3 team design review |
| S1-R01-T2 | Maintain the React-to-placeholder-recognition-to-controller-to-command path | Integrated PR, tests, demo screenshot or recording, named reviewer | Sep 17 |
| S1-R01-T3 | Document setup, risks, traceability, and review a different layer | README/setup notes, risk log, traceability document, peer-review record | Sep 17 |

## Branch and PR workflow

1. Create a feature branch from `develop`.
2. Use a task-focused branch name, for example `feature/S1-R01-vertical-slice`.
3. Keep commits small and describe the layer or behavior changed.
4. Run the documented verification commands before opening a PR.
5. Open the PR into `develop` with a named reviewer from another layer.
6. Include test output and a short demonstration artifact when relevant.
7. Merge only after review comments are resolved and required checks pass.

## Sprint evidence model

Each implementation claim should have at least one reproducible artifact:

| Claim | Evidence |
|---|---|
| Architecture boundary is defined | Decision note and event contract |
| Vertical path works | Test output plus screenshot or recording |
| Setup is reproducible | README commands and environment verification |
| Risks are managed | Risk log with owner and mitigation |
| Cross-layer collaboration occurred | Peer-review record with PR link and findings |

## MVP boundary for Sprint 1

The goal is a demonstrable contract-level vertical slice, not production-ready computer vision. Camera capture, ML inference, transport, and performance tuning remain outside the Sprint 1 acceptance boundary unless the team explicitly changes scope.
