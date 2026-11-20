# S4-R01-T1 Post-Midterm Plan

**Jira:** SCRUM-167
**Owner:** Joon Rho, R01
**Status:** Draft for team review. Teammate review has not happened yet.

## What this plan is based on

I did not have the instructor's written midterm feedback. This plan uses three sources instead: the midterm baseline recorded in the Sprint 4 control proposal, the Sprint 3 gap analysis in `sprints/S3-R01-T1-Prototype-Gap-Analysis.md`, and the Jira board as read during this task. If written midterm feedback exists, add it under Open questions.

Jira now shows Sprint 4 as closed. SCRUM-167, SCRUM-168 and SCRUM-169 moved into Sprint 5, whose goal is testing, metrics, accessibility, performance and a release candidate. The plan below fits that goal, because most of the remaining R01 work is validation, documentation and regression coverage and not new features.

## Where things stand

At the midterm, session aware command coordination, a keyboard presentation adapter, a Windows helper and the Python test setup were in place. Custom gestures and profiles, a live link between the frontend and the Python side, and focus aware execution were still open.

Since then, Control 01 added a command policy and validated gesture bindings in the controller. That work is merged into develop. Teammates have also moved forward on the pieces that will feed profiles.

| Owner | Jira | What it covers | Status in Jira |
|---|---|---|---|
| Diego | SCRUM-56 | Static gesture recognition and prototype custom classifier support | Done |
| Diego | SCRUM-58 | Evaluate static gesture recognition | In Progress |
| Eric | SCRUM-64 | Guided gesture enrollment backend prototype | In Progress |
| Eric | SCRUM-66 | Validate the enrollment workflow | To Do |
| Eric | SCRUM-57 | Harden next and previous, expose status to controller and UI | To Do |
| Andres | SCRUM-87 | Calibration and profile UI | Done |

## Priorities

| Priority | Work | Why |
|---|---|---|
| P0 | One validated path from a profile to a keystroke, SCRUM-168 | Custom gestures from Diego, enrollment from Eric and the profile UI from Andres will all produce gesture ids and mappings. Without one checked path, each of them is a new way to reach the keyboard |
| P0 | Control 01 evidence, SCRUM-170 to SCRUM-173 | The code is merged. The CI and review evidence still has to be linked |
| P1 | Agree the four contracts with Diego, Andres and Eric, this task | Nobody should build against a contract the others have not seen |
| P1 | Architecture notes, traceability and regression coverage, SCRUM-169 | Changed features need records and tests before a release candidate |
| P2 | Live link between the React app and the Python side | No transport exists. The session page is still a simulation. This needs a team decision and is not planned in any R01 task |
| P2 | Numeric slide jump | Deferred since Sprint 3. It needs a gesture and command design first |
| P2 | Window focus and adapter hardening | Eric owns it under SCRUM-57. Command allowlisting does not solve it |

## Dependencies

| What R01 needs | From | Why it matters | State |
|---|---|---|---|
| The set of gesture ids the recognizer can emit | Diego | The profile loader can reject a mapping for a gesture that never fires. It already accepts that set, but nothing passes it in yet | Open |
| Where enrollment writes its result and in what shape | Eric | Enrolled gestures should arrive as a profile that fits the schema, or be converted into one | Open |
| How the profile UI saves or sends a profile | Andres | The UI should produce the same schema the loader reads | Open |
| Adapter status beyond true or false | Eric | The controller only sees whether a key was attempted | Open |
| Test folders picked up by CI | Nathan | New tests sit in the existing unit and integration folders, so no workflow change is needed | None needed |

## Decisions made in this task

These are my proposals. They need the team's confirmation.

1. The `end` command cannot be bound by a profile. This came from Control 01.
2. A profile can be applied only while the session is IDLE, PAUSED or ENDED. It is refused while RUNNING, so bindings never change while gestures are being acted on.
3. Profile files are JSON, schema version 1, at most 64 KB, with exactly the fields version, name and bindings.
4. The loader checks the shape of a gesture id. It checks that the recognizer emits the id only when the caller passes the recognizer's gesture set.

## Open questions

- Is there written midterm feedback that changes these priorities?
- Is a live link between the UI and the Python side needed for the release candidate?
- Is numeric slide jump in scope?
- Should ending a session while paused become valid? The session state model already lists this as open.
