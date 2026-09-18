# Architecture Decision Note: Sprint 1

**Decision owner:** Project team
**Status:** Draft for team design review
**Scope:** Sprint 1 MVP vertical slice

## Decision

Use a layered event-driven boundary:

`React UI -> recognition provider -> controller -> presentation adapter`

The current browser demonstration uses a deterministic placeholder recognition function. The Python package defines the shared recognition and command contracts and keeps presentation control behind the `PresentationAdapter` abstraction.

## Why this boundary

- The UI can evolve without knowing camera, model, or OS-level input details.
- Recognition can be replaced without rewriting command mapping.
- Presentation adapters can support keyboard control first and other applications later.
- Each boundary can be tested independently, while the vertical slice provides integration evidence.

## Responsibilities and non-responsibilities

| Boundary | Owns | Must not own |
|---|---|---|
| React UI | Session state, user-visible controls, accessibility states | `pyautogui`, model inference, adapter implementation |
| Recognition | Producing `RecognitionEvent` values | Presentation side effects or command execution |
| Controller | Gesture-to-command mapping and adapter invocation | Camera capture or UI rendering |
| Presentation adapter | Translating normalized commands into app-specific actions | Gesture interpretation or UI state |
| Evidence/docs | Setup, risks, traceability, review records | Runtime business logic |

## Event contract

Recognition events contain `gesture`, `confidence` in `[0, 1]`, and `source`. Command events contain a normalized command, source gesture, and metadata. `Gesture.NONE` produces no command.

The detailed contract is documented in [Observer Event Contract](observer-event-contract.md).

## MVP scope

Included:

- Dashboard and Session UI shell
- Deterministic placeholder recognition
- Gesture-to-command controller mapping
- Keyboard presentation adapter boundary
- Unit tests for contracts and controller behavior

Deferred:

- Camera capture
- ML inference and model evaluation
- Browser-to-Python transport
- Multi-application adapters
- Latency/performance tuning
- Persistent telemetry and production logging

## Key decisions and consequences

1. **Typed event contracts:** reduces ambiguity between layers, but requires coordinated changes when fields or gestures change.
2. **Adapter abstraction:** supports future presentation targets, but the keyboard adapter remains host-dependent.
3. **Placeholder recognition:** enables early integration testing, but does not prove real gesture accuracy.
4. **Local browser path in Sprint 1:** keeps the demo simple, but transport integration remains a later milestone.

## Acceptance evidence

- Architecture and contract notes reviewed during team design review.
- Integrated PR has a named reviewer.
- Unit tests cover valid and invalid recognition events, gesture mapping, and the no-op gesture.
- README contains reproducible setup and verification commands.
