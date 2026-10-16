# S3-R02-T1 Pre-Demo Readiness Review

## Purpose

Review the current SlideKick frontend before the midterm demo (Oct 22) and
prioritize what needs polish in SCRUM-84.

This supports S3-R02-T1 / SCRUM-83. The ticket was originally written as a
review of the midterm demo, but the demo hasn't happened yet, so this is a
pre-demo readiness review of the current prototype instead.

## What was reviewed

- Session page at `http://localhost:5173/session` (`develop` branch), clicked
  through manually, including keyboard-only navigation
- Session components in `frontend/src/session/` and `SessionPage.tsx`
- Dashboard and Settings pages
- Compared against `docs/ui-states.md`, `docs/session-state-model.md`, and the
  `useSession` hook added in S3-R01 (`frontend/src/core/useSession.ts`)

## Findings

Severity: **High** = should be fixed before the demo, **Medium** = fix if
time allows, **Low** = known limitation or team decision.

| # | Area | Problem | Expected | Severity | SCRUM-84? |
|---|---|---|---|---|---|
| 1 | Session lifecycle | No Start or End session control, only Pause/Resume | Ready offers a clear Start action; Active/Paused offer End (`ui-states.md`) | High | Yes |
| 2 | Session lifecycle | Session page uses its own mock states (`loading/ready/active/paused/error`) instead of the `useSession` hook (`idle/running/paused/ended`); no Ended state in the UI | Session page driven by `useSession`, matching `session-state-model.md` | High | Yes |
| 3 | Gesture feedback | Gestures still show as detected (feedback + toast) while paused | Paused gestures don't appear to control the presentation | High | Yes |
| 4 | Session lifecycle | No message for Active or Paused; they differ only by badge text and button | Paused shows "Gesture recognition paused. Gestures will not control your presentation." (`ui-states.md`) | High | Yes |
| 5 | Gesture feedback | Shows the gesture ("Next") but not the resulting action | Show both, e.g. "Next → Next slide" (`ui-states.md`) | Medium | If time |
| 6 | Error handling | No recovery action (Retry); presentation disconnected has no explanation | Plain error message plus a recovery action where possible | Medium | If time |
| 7 | Accessibility | Six separate `role="status"` regions; each gesture is announced twice (feedback + toast) | Fewer live regions so screen readers aren't flooded | Medium | If time |
| 8 | Demo flow | Demo controls can jump straight to any state (e.g. Ready → Paused) | Once on `useSession`, demo controls only simulate outside inputs (camera, presentation, gestures) | Low | With #2 |
| 9 | Navigation | Dashboard and Settings are placeholder text | Fine for the midterm; list as a known limitation | Low | No |
| 10 | Session lifecycle | `ui-states.md` says Paused should offer resume or end, but `session-state-model.md` (updated in PR #39) only allows ending from Running | Follow the state model for now: End is disabled while paused. If the team changes this, the controller, state model, and `useSession` change together | Low | Yes |
| 11 | Demo flow | Frontend has no connection to the backend; everything on the Session page is mock data | Flag to team for the midterm vertical slice | Low | No (team) |

Carried over from the Sprint 2 walkthrough
(`sprints/S2-R02-T3-Usability-Walkthrough.md`): mock confidence values were
mistaken for real output. Worth a visible "demo data" label while they're
still hardcoded.

## Priorities for SCRUM-84

1. Drive the Session page with `useSession` and add Start/End controls (#1, #2, #8)
2. Block gesture feedback while paused (#3)
3. Add Active/Paused messages (#4)
4. If time allows: gesture action labels, error recovery, fewer live regions (#5–#7)

For #10, the End control follows the current state model (disabled while
paused). #11 goes to the team, not SCRUM-84.

## Not reviewed

Gesture recognition accuracy, the presentation adapter, and backend behavior
are outside R02's scope and covered by other roles.
